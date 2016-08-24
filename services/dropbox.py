"""File service implementation for Dropbox file storage service.

NOTE: Dropbox currently does not support file search by hash
NOTE: Dropbox file name search results may not be available for ~30 minutes or
      more.

Created: 08/17/2016
Creator: Nathan Palmer
"""

from fileservice import fileServiceInterface
from cazobjects import CazFile
import dropbox
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

    def get_file(self, name=None, md5=None, sha1=None):
        """Get a file from Dropbox using the name or hashes."""
        raise NotImplementedError


# Register our handler
fileServiceInterface.register(dropboxHandler)
