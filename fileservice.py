"""
Core module for External File Service Interface.

This module defines the base External File Service Interface used by data/file
providers such as Amazon S3, Microsoft Azure, Google Drive, etc. access modules.

Created: 08/11/2016
Creator: Nathan Palmer
"""

import os
import sys
import logging
from abc import ABCMeta, abstractmethod


class fileServiceInterface(metaclass=ABCMeta):
    """External File Service Interface.

    Initializers for derived classes are required to accept the following arguments:
        config_fields (dict): Configuration dictionary loaded from file.
        logging        (log): Standard python logging interface
    """

    @staticmethod
    @abstractmethod
    def get_service_type():
        """Return a string id for the file service type handled."""
        raise NotImplementedError

    @abstractmethod
    def convert_file(self, item):
        """
        Convert from service specfic file format to cazobject file format.

        Args:
            item (object): Service specific representation of a file.

        Returns:
            cazobject.CazFile
        """
        raise NotImplementedError

    def convert_files(self, items):
        """
        Convert a list of service specfic file entries to cazobject entries.

        Args:
            items (object[]): Service specific representation of a list of files.

        Returns:
            List of cazobject.CazFile entries
        """
        results = []
        for i in items:
            results.append(self.convert_file(i))

        return results

    @abstractmethod
    def find_file(self, name=None, md5=None, sha1=None):
        """
        Search for a file by name or hash.

        If a mixture of input parameters are included then the search
        will walk through in the following manner:
            1. If name is defined then look by name
            2. If not found and md5 is defined then look by md5
            3. If not found and sha1 is defined then look by sha1
            4. If not found raise.

        Args:
            name (string): Filename to find.
            md5 (string): MD5 hash of the file to find.
            sha1 (string): SHA1 hash of the file to find.

        Returns:
            List of CazFile objects matching the request parameters.
        """
        raise NotImplementedError

    @abstractmethod
    def get_file(self, name=None, md5=None, sha1=None):
        """
        Search for a file by name or hash and download a copy.

        If a mixture of input parameters are included then the search
        will walk through in the following manner:
            1. If name is defined then look by name
            2. If not found and md5 is defined then look by md5
            3. If not found and sha1 is defined then look by sha1
            4. If not found raise.

        Args:
            name (string): Filename to find.
            md5 (string): MD5 hash of the file to find.
            sha1 (string): SHA1 hash of the file to find.

        Returns:
            List of files matching the request parameters.
        """
        raise NotImplementedError
