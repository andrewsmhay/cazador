"""
Cazador file/cloud service investigator objects module.

This portion of the module handles the simple object types expected as the
result of a Cazador operation.

Created: 08/24/2016
Creator: Nathan Palmer
"""


class CazFile:
    """Simple file metadata object."""

    def __init__(self, file_id, name, parent, sha1=None, md5=None, path=None):
        """CazFile initializer."""
        self.file_id = str(file_id) if not None else None
        self.name = str(name) if not None else None
        self.parent = str(parent) if not None else None
        self.sha1 = str(sha1) if not None else None
        self.md5 = str(md5) if not None else None
        self.path = str(path) if not None else None

    def __str__(self):
        """String print helper."""
        return """[{} ({})] Parent:{}
Path:{}
SHA1:{} MD5:{}""".format(self.name,
                         self.file_id,
                         self.parent,
                         self.path,
                         self.sha1,
                         self.md5)
