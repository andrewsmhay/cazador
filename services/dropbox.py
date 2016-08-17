"""File service implementation for Dropbox file storage service.

NOTE: Dropbox currently does not support file search by hash
NOTE: Dropbox file name search results may not be available for ~30 minutes or
      more.

Created: 08/11/2016
Creator: Nathan Palmer
"""

from fileservice import fileServiceInterface
import dropbox


class dropboxHandler(fileServiceInterface):
    """Dropbox cloud service handler."""

    def __init__(self, config_fields, logging):
        """
        Initialize the Dropbox handler using configuration dictionary fields.

        Args:
            config_fields (dict): String dictionary from the configuration segment
            logging        (log): Standard python logging interface

        Configuration Fields:
            access_token (str): Repository access token
        """
        self.client = dropbox.Dropbox(config_fields["access_token"])
        self.logging = logging

        self.folders = []
        try:
            raw = config_fields["folgers"].split(';')
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
        """Return the type of file service (Amazon)."""
        return "Dropbox"

    def find_file(self, name=None, md5=None, sha1=None):
        """Find one or more files using the name and/or hash in Dropbox."""
        if not name and (md5 or sha1):
            """Dropbox doesn't support hash searching at this time."""
            self.logging.error("Dropbox does not currently support hash searching.")
            raise ValueError("Dropbox does not support hash only searching.")

        matches = []
        for f in self.folders:
            start = 0
            while True:
                res = self.client.files_search(f, name, start=start)
                if len(res.matches):
                    # matches were found
                    for m in res.matches:
                        matches.append(m)
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
