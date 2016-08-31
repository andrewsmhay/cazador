"""
Cazador file/cloud service investigator scanning module.

This module handles walking through a given service provider to scan for content
within the files stored. This will create temporary copies of each file locally
to perform the scan.

Created: 08/29/2016
Creator: Nathan Palmer
"""

import io
import os
import tika
from tika import parser
import cazobjects


def create_temp_name(temp_dir, file_id):
    """Create a temporary file name based on the ID."""
    return os.path.join(temp_dir,
                        "caz_{}".format(os.path.basename(file_id)))


def search_content(file_path, expressions):
    """Open a file and search it's contents against a set of RegEx."""
    matches = []
    count = 0
    data = parser.from_file(file_path)
    # Read into an I/O buffer for better readline support
    content = io.StringIO(data['content'])
    # TODO this may create a very large buffer for larger files
    # We may need to convert this to a while readline() loop
    for line in content.readlines():
        count += 1  # count the number of lines
        if line:
            for rex in expressions:
                # Check if the line matches all the expressions
                res = rex.regex.search(line)
                if res:
                    # If there's a match append to the list
                    matches.append(cazobjects.CazRegMatch(res,
                                                          file_path,
                                                          count,
                                                          rex.name))
    return matches
