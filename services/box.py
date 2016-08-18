"""File service implementation for Box file storage service.

Created: 08/18/2016
Creator: Nathan Palmer
"""

from fileservice import fileServiceInterface
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

    def find_file(self, name=None, md5=None, sha1=None):
        """Find one or more files using the name and/or hash in Box."""
        matches = []

        if not name and not sha1 and md5:
            logger.error("Box does not support MD5 hash searching.")
            return matches

        queries = []
        if name:
            queries.append(name)
        if sha1:
            queries.append("sha1={}".format(sha1))

        for f in self.folders:
            # There doesn't seem to be support for chaining...
            f_ids = None
            if not f == '':
                box_folder = self.client.search(f, limit=1, offset=0, result_type="folder")
                for x in box_folder:
                    f_ids = [x]
                    # break shouldn't be necessary... but why not
                    break

            for q in queries:
                res = self.client.search(q, limit=200, offset=0, ancestor_folders=f_ids)
                # matches were found
                for m in res:
                    # pprint.pprint(m.name)
                    # pprint.pprint(m.sha1)
                    m_path = ""
                    for x in m.path_collection["entries"]:
                        m_path += "{}/".format(x["name"])
                    # pprint.pprint("{}{}".format(m_path, m.name))
                    matches.append(m)

        return matches

    def get_file(self, name=None, md5=None, sha1=None):
        """Get a file from Box using the name or hashes."""
        raise NotImplementedError


# Register our handler
fileServiceInterface.register(boxHandler)
