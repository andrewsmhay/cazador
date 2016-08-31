"""
Cazador file/cloud service investigator objects module.

This portion of the module handles the simple object types expected as the
result of a Cazador operation.

Created: 08/24/2016
Creator: Nathan Palmer
"""
import hashlib
import re


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


class CazRegEx:
    """Simple wrapper for a compiled named regular expression."""

    def __init__(self, name, expression):
        """CazRegEx initializer."""
        self.name = name
        # Compile the regex so it can be more efficiently reused
        self.regex = re.compile(expression)


class CazRegMatch:
    """Simple wrapper for a regex match."""

    def __init__(self, match, file_path, line, regex_name):
        """CazRegMatch initializer."""
        # store only a hash of the value
        self.hash = hashlib.sha1(match.group(0).encode('utf-8')).hexdigest()
        self.expression_name = regex_name
        self.location = (match.start(), match.end())
        self.line_number = line
        self.file_path = file_path

    def __str__(self):
        """String print helper."""
        return "{} detected a match for {} in {} at location {} line {}.".format(self.hash,
                                                                                 self.expression_name,
                                                                                 self.file_path,
                                                                                 self.location,
                                                                                 self.line_number)
