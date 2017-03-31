"""File service implementation for Dropbox file storage service.

NOTE: Dropbox currently does not support file search by hash
NOTE: Dropbox file name search results may not be available for ~30 minutes or
      more.

Created: 08/17/2016
Creator: Nathan Palmer
"""

import os
from fileservice import fileServiceInterface
from cazobjects import CazFile
from cazscan import search_content, create_temp_name
import dropbox
from dropbox.files import FileMetadata
import logging

logger = logging.getLogger(__name__)


class dropboxHandler(fileServiceInterface):
    """Dropbox cloud service handler."""

    def __init__(self, config_fields):
        """
        Initialize the Dropbox handler using configuration dictionary fields.

        Args:
            config_fields (dict): String dictionary from the configuration segment

        Configuration Fields:
            access_token (str): Repository access token
        """
        self.client = dropbox.Dropbox(config_fields["access_token"])

        self.folders = []
        try:
            raw = config_fields["folders"].split(';')
            for b in raw:
                if b:
                    # Only add buckets that are not null or empty strings
                    if b == '/':
                        self.folders.append('')
                    else:
                        self.folders.append(b)
        except:
            self.folders.append('')

    @staticmethod
    def get_service_type():
        """Return the type of file service (Dropbox)."""
        return "Dropbox"

    def convert_file(self, item):
        """Convert the file details into a CazFile."""
        md = item.metadata
        return CazFile(md.id,
                       md.name,
                       md.parent_shared_folder_id,
                       path=md.path_display)

    def find_file(self, name=None, md5=None, sha1=None):
        """Find one or more files using the name and/or hash in Dropbox."""
        if not name and (md5 or sha1):
            """Dropbox doesn't support hash searching at this time."""
            logger.error("Dropbox does not currently support hash searching.")
            raise ValueError("Dropbox does not support hash only searching.")

        matches = []
        # TODO: https://www.dropbox.com/developers/reference/content-hash
        for f in self.folders:
            start = 0
            while True:
                res = self.client.files_search(f, name, start=start)
                if len(res.matches):
                    # matches were found
                    for m in res.matches:
                        matches.append(self.convert_file(m))
                if res.more:
                    start = res.start
                else:
                    break

        return matches

    def scan_files(self, temp_dir, expressions):
        """
        Scan all files for any content matches.

        Args:
            expressions (CazRegExp[]) List of regular expressions for content comparison
        """
        matches = []

        for f in self.folders:
            try:
                res = self.client.files_list_folder(f, recursive=True)

                while True:
                    for x in res.entries:
                        # DBX FileMetadata/FolderMetadata
                        if isinstance(x, FileMetadata):
                            f_path = create_temp_name(temp_dir, x.name)
                            try:
                                # If it's a file... download and process
                                self.client.files_download_to_file(f_path, x.path_display)
                                logger.debug("Processing file {}...{}".format(x.name, f_path))
                                matches.extend(search_content(f_path, expressions))
                            except Exception as ex:
                                logger.error("Unable to parse contents in file {}. {}".format(x.name,
                                                                                              ex))

                            try:
                                # Clean up the temporary file
                                os.remove(f_path)
                            except Exception as ex:
                                logger.error("Unable to clean up temporary file {}. {}".format(f_path,
                                                                                               ex))

                    if not res.has_more:
                        break
                    else:
                        # Get the next set
                        res = self.client.files_list_folder_continue(res.cursor)

            except Exception as ex:
                logger.error("Unable to process folder {}. {}".format(f, ex))

        return matches

    def get_file(self, name=None, md5=None, sha1=None):
        """Get a file from Dropbox using the name or hashes."""
        raise NotImplementedError


# Register our handler
fileServiceInterface.register(dropboxHandler)
