"""File service implementation for Google Drive file storage service.

Created: 08/23/2016
Creator: Nathan Palmer
"""

from fileservice import fileServiceInterface
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
    CLIENT_SECRET_FILE = 'client_secret.json'

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
        """Return the type of file service (Google Drive)."""
        return "GoogleDrive"

    def find_file(self, name=None, md5=None, sha1=None):
        """Find one or more files using the name and/or hash in Google Drive."""
        matches = []

        if not name and (sha1 or md5):
            logger.error("Google Drive does not support SHA1 or MD5 hash searching.")
            return matches

        try:
            # results = self.client.files().list(
            #    pageSize=100, fields="nextPageToken, files(id, name)").execute()
            nextPage = ""
            query = ""
            if name:
                query += " name contains '{}'".format(name)

            """
            if md5:
                if query:
                    query + " or "
                query += " md5Checksum contains '{}'".format(md5)
            """

            while nextPage is not None:
                results = self.client.files().list(
                    pageSize=100, q=query).execute()
                items = results.get('files', [])
                try:
                    nextPage = results.get('nextPageToken', None)
                except:
                    nextPage = None

                if not items:
                    logger.info('No files found.')
                else:
                    logger.info('Files:')
                    for item in items:
                        logger.info('{0} ({1})'.format(item['name'], item['id']))
                        matches.append(item)

            for f in self.folders:
                pass
        except AccessTokenRefreshError:
            # The AccessTokenRefreshError exception is raised if the credentials
            # have been revoked by the user or they have expired.
            logger.error('Unable to execute command. The access tokens have been'
                         ' revoked by the user or have expired.')

        return matches

    def get_file(self, name=None, md5=None, sha1=None):
        """Get a file from Google Drive using the name or hashes."""
        raise NotImplementedError


# Register our handler
fileServiceInterface.register(googledriveHandler)
