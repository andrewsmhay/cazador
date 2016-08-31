"""File service implementation for Box file storage service.

Created: 08/18/2016
Creator: Nathan Palmer
"""

from fileservice import fileServiceInterface
from cazobjects import CazFile
from cazscan import search_content, create_temp_name
import os
from boxsdk import OAuth2
import boxsdk
import logging
import bottle
from threading import Thread, Event
import webbrowser
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server
logger = logging.getLogger(__name__)


class boxHandler(fileServiceInterface):
    """Box cloud service handler."""

    class StoppableWSGIServer(bottle.ServerAdapter):
        def __init__(self, *args, **kwargs):
            super(boxHandler.StoppableWSGIServer, self).__init__(*args, **kwargs)
            self._server = None

        def run(self, app):
            server_cls = self.options.get('server_class', WSGIServer)
            handler_cls = self.options.get('handler_class', WSGIRequestHandler)
            self._server = make_server(self.host, self.port, app, server_cls, handler_cls)
            self._server.serve_forever()

        def stop(self):
            self._server.shutdown()

    def __init__(self, config_fields):
        """
        Initialize the Box handler using configuration dictionary fields.

        Args:
            config_fields (dict): String dictionary from the configuration segment

        Configuration Fields:
            access_token (str): Repository access token
        OAuth Interactive Configuration Fields:
            local_auth_ip (str): Local IP address to use for OAuth redirection
            local_auth_port (str): Local port to use for OAuth redirection
            client_id (str): Client Id to use for OAuth validation
            client_secret (str): Client secret to use for OAuth validation
        """
        auth_code = {}
        auth_code_available = Event()
        local_oauth_redirect = bottle.Bottle()

        @local_oauth_redirect.get('/')
        def get_token():
            auth_code['auth_code'] = bottle.request.query.code
            auth_code['state'] = bottle.request.query.state
            auth_code_available.set()
        try:
            access_token = config_fields["access_token"]
            oauth = OAuth2(client_id="",
                           client_secret="",
                           access_token=access_token)
        except:
            # If we don't have an access_token perform OAuth validation
            try:
                host = config_fields['local_auth_ip']
            except:
                host = 'localhost'

            try:
                port = config_fields['local_auth_port']
            except:
                port = 8080

            local_server = boxHandler.StoppableWSGIServer(host=host, port=port)
            server_thread = Thread(target=lambda: local_oauth_redirect.run(server=local_server))
            server_thread.start()

            oauth = OAuth2(client_id=config_fields["client_id"],
                           client_secret=config_fields["client_secret"])

            auth_url, csrf_token = oauth.get_authorization_url('http://{}:{}'.format(host,
                                                                                     port))
            webbrowser.open(auth_url)
            logger.info("waiting for authentication token.")

            auth_code_available.wait()
            local_server.stop()
            assert auth_code['state'] == csrf_token
            access_token, refresh_token = oauth.authenticate(auth_code['auth_code'])

        self.client = boxsdk.Client(oauth)

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
        """Return the type of file service (Box)."""
        return "Box"

    def convert_file(self, item):
        """Convert the file details into a CazFile."""
        m_path = ""
        path_entr = []
        try:
            path_entr = item.path_collection["entries"]
        except:
            # Some of the items don't have it... try a direct request
            pc = item.get(['path_collection', 'id', 'parent', 'name', 'sha1'])
            if pc:
                item = pc

        for x in path_entr:
            m_path += "{}/".format(x["name"])

        try:
            caz = CazFile(item.id,
                          item.name,
                          item.parent,
                          sha1=item.sha1,
                          path=m_path)
        except Exception as ex:
            logger.error("Unable to translate result item. {}".format(ex))
            caz = None
        return caz

    def _build_folder_list(self):
        """Convert the folder names into a list of Box Folder objects."""
        box_folders = []
        for f in self.folders:
            # Build a set of Box Folder entries for searching
            if not f == '':
                bfs = self.client.search(f, limit=1, offset=0, result_type="folder")

                for x in bfs:
                    box_folders.append(x)
                    # break shouldn't be necessary... but why not
                    break
            else:
                box_folders.append(self.client.folder('0'))
        return box_folders

    def _walk_directories_with_function(self, operation, folder_ids):
        """Crawl the contents of the repository passing each result an operation.

        This operation walks through the entire heirarchy and may be expensive and
        time consuming based on the size and depth of the repository.
        """
        processed_fids = []

        # api limit on results
        limit = 1000
        logger.debug("Processing {} initial folders".format(len(folder_ids)))
        while folder_ids:
            # Continue to walk through the folder ids until none are left
            box_folder = folder_ids.pop(0)
            fid = box_folder._object_id

            if fid in processed_fids:
                # Don't double work if we already processed the ID
                logger.error("FID {} already processed".format(fid))
                continue
            # box_folder = self.client.folder(fid)
            offset = 0

            while True:
                items = box_folder.get_items(limit, offset=offset)
                logger.debug("Analyzing {} items in folder id {}. Total analyzed {}".format(len(items),
                                                                                            fid,
                                                                                            offset))
                for x in items:
                    if x.type == 'folder':
                        if x.id not in processed_fids:
                            folder_ids.append(x)
                    elif x.type == 'file':
                        operation(x)

                if len(items) < limit:
                    logger.debug("Finished folder {} processing".format(fid))
                    # If we received a set smaller than the limit... we are done
                    break
                else:
                    logger.debug("Retrieving more items from folder {}".format(fid))
                    offset += limit

            processed_fids.append(fid)

    def _find_by_sha1(self, sha1, folder_ids):
        """Crawl the contents of the repository to find the object based on SHA1.

        This operation walks through the entire heirarchy and may be expensive and
        time consuming based on the size and depth of the repository. This type of
        operation is a last ditch effort due to limited support for direct hash
        searching.
        """
        if not sha1:
            raise ValueError("No valid search hash specified.")

        logger.warn("Box does not officially support SHA1 searching."
                    " This operation will walk your entire heirarchy comparing"
                    " file metadata.")

        matches = []

        def check_file_sha1(box_obj):
            if box_obj.sha1 == sha1:
                matches.append(self.convert_file(box_obj))

        self._walk_directories_with_function(check_file_sha1, folder_ids)

        return matches

    def find_file(self, name=None, md5=None, sha1=None):
        """Find one or more files using the name and/or hash in Box."""
        matches = []

        if not name and not sha1 and md5:
            logger.error("Box does not support MD5 hash searching.")
            return matches

        if not name and not sha1:
            logger.error("No valid search criteria supplied.")
            return matches

        box_folders = self._build_folder_list()

        if name:
            res = self.client.search(name, limit=200, offset=0, ancestor_folders=box_folders)
            # matches were found
            for m in res:
                matches.append(self.convert_file(m))

        if sha1:
            # add any matches to the existing list
            matches.extend(self._find_by_sha1(sha1, box_folders))

        return matches

    def scan_files(self, temp_dir, expressions):
        """
        Scan all files for any content matches.

        Args:
            expressions (CazRegExp[]) List of regular expressions for content comparison
        """
        matches = []

        box_folders = self._build_folder_list()

        def check_contents(box_obj):
            f_path = create_temp_name(temp_dir, box_obj.name)
            logger.debug("Processing file {}...{}".format(box_obj.name, f_path))
            f = open(f_path, 'wb')
            box_obj.download_to(f)
            f.close()
            try:
                matches.extend(search_content(f_path, expressions))
            except Exception as ex:
                logger.error("Unable to parse content in file {}. {}".format(box_obj.name, ex))

            try:
                os.remove(f_path)
            except Exception as ex:
                logger.error("Unable to clean up temprary file {}. {}".format(f_path, ex))

        self._walk_directories_with_function(check_contents, box_folders)

        return matches

    def get_file(self, name=None, md5=None, sha1=None):
        """Get a file from Box using the name or hashes."""
        raise NotImplementedError


# Register our handler
fileServiceInterface.register(boxHandler)
