"""File service implementation for Google Drive file storage service.

Created: 08/23/2016
Creator: Nathan Palmer
"""

from fileservice import fileServiceInterface
from cazobjects import CazFile
import logging
logger = logging.getLogger(__name__)

import httplib2
import os
from apiclient import discovery
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow


class googledriveHandler(fileServiceInterface):
    """Google Drive cloud service handler."""

    SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'
    FOLDER_MIME = "application/vnd.google-apps.folder"

    class oauth_flags(object):
        def __init__(self):
            self.short_url = True
            self.noauth_local_webserver = False
            self.logging_level = 'ERROR'
            self.auth_host_name = 'localhost'
            self.auth_host_port = [8080, 9090]

    def __init__(self, config_fields):
        """
        Initialize the Google Drive handler using configuration dictionary fields.

        Args:
            config_fields (dict): String dictionary from the configuration segment

        Configuration Fields:
            access_token (str): Repository access token
        OAuth Interactive Configuration Fields:
            client_id (str): Client Id to use for OAuth validation
            client_secret (str): Client secret to use for OAuth validation
            cred_file (str): Full filepath to store credentials used for access.
        """
        flow = OAuth2WebServerFlow(config_fields["client_id"],
                                   config_fields["client_secret"],
                                   self.SCOPES)
        try:
            storage = Storage(config_fields["cred_file"])
        except:
            storage = Storage(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                           "gdc.dat"))
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            credentials = tools.run_flow(flow,
                                         storage,
                                         flags=googledriveHandler.oauth_flags())

        # Create an httplib2.Http object to handle our HTTP requests, and authorize it
        # using the credentials.authorize() function.
        http = httplib2.Http()
        http = credentials.authorize(http)
        self.client = discovery.build('drive', 'v3', http=http)

    @staticmethod
    def get_service_type():
        """Return the type of file service (Google Drive)."""
        return "GoogleDrive"

    def convert_file(self, item):
        """Convert the file details into a CazFile."""
        return CazFile(item.get('id', None),
                       item.get('name', None),
                       item.get('parents', None),
                       md5=item.get('md5Checksum', None))

    def _run_file_search_query(self,
                               query,
                               item_check,
                               fields="nextPageToken, files(id, name, kind, mimeType, md5Checksum, parents)"):
        nextPage = ""
        try:
            nextPage = ""

            while nextPage is not None:
                results = self.client.files().list(pageSize=1000,
                                                   q=query,
                                                   fields=fields,
                                                   pageToken=nextPage,
                                                   spaces="drive").execute()
                items = results.get('files', [])
                try:
                    nextPage = results.get('nextPageToken', None)
                except:
                    nextPage = None

                if not items:
                    logger.debug('No files found.')
                else:
                    logger.debug('{} Files found.'.format(len(items)))
                    for item in items:
                        item_check(item)

        except AccessTokenRefreshError:
            # The AccessTokenRefreshError exception is raised if the credentials
            # have been revoked by the user or they have expired.
            logger.error('Unable to execute command. The access tokens have been'
                         ' revoked by the user or have expired.')

    def _find_by_md5(self, md5):
        """Crawl the contents of the repository to find the object based on the tags.

        This operation walks through the entire heirarchy and may be expensive and
        time consuming based on the size and depth of the repository. This type of
        operation is a last ditch effort due to limited support for direct hash
        searching.
        """
        if not md5:
            raise ValueError("No valid search hash specified.")

        matches = []

        def md5_item_check(item):
            check = item.get('md5Checksum', None)
            if check == md5:
                matches.append(self.convert_file(item))

        self._run_file_search_query("", md5_item_check)
        return matches

    def find_file(self, name=None, md5=None, sha1=None):
        """Find one or more files using the name and/or hash in Google Drive."""
        matches = []

        if not name and not md5 and sha1:
            logger.error("Google Drive does not support SHA1 hash searching.")
            return matches

        if md5:
            logger.warn("Google Drive does not officially support MD5 searching."
                        " This operation will walk your entire heirarchy comparing"
                        " file metadata.")

        def std_item_check(item):
            matches.append(self.convert_file(item))

        try:
            if name:
                self._run_file_search_query("name contains '{}'".format(name),
                                            std_item_check)
        except AccessTokenRefreshError:
            # The AccessTokenRefreshError exception is raised if the credentials
            # have been revoked by the user or they have expired.
            logger.error('Unable to execute command. The access tokens have been'
                         ' revoked by the user or have expired.')

        if md5:
            matches.extend(self._find_by_md5(md5))

        return matches

    def get_file(self, name=None, md5=None, sha1=None):
        """Get a file from Google Drive using the name or hashes."""
        raise NotImplementedError


# Register our handler
fileServiceInterface.register(googledriveHandler)
