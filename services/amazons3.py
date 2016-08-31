"""File service implementation for the Amazon S3 cloud service.

Created: 08/11/2016
Creator: Nathan Palmer
"""

import os
from fileservice import fileServiceInterface
from cazobjects import CazFile
from cazscan import search_content, create_temp_name
import boto3
import botocore
import logging
logger = logging.getLogger(__name__)


class amazonS3Handler(fileServiceInterface):
    """Amazon cloud service handler."""

    def __init__(self, config_fields):
        """
        Initialize the Amazon S3 handler using configuration dictionary fields.

        Args:
            config_fields (dict): String dictionary from the configuration segment

        Configuration Fields:
            access_key_id (str): Repository access key id
            secret_key (str): Repository secret key for authentication
            region (str): Repository region code
            buckets (str): Semicolon separated list of buckets to search
            filename_crawl (bool): Support failing back to a filename wildcard crawl
        """
        self.client = boto3.resource("s3",
                                     region_name=config_fields["region"],
                                     aws_access_key_id=config_fields["access_key_id"],
                                     aws_secret_access_key=config_fields["secret_key"])

        self.buckets = []
        raw_buckets = config_fields["buckets"].split(';')
        for b in raw_buckets:
            if b:
                # Only add buckets that are not null or empty strings
                self.buckets.append(b)

        try:
            self.filename_crawl = config_fields["filename_crawl"].lower() == 'true'
        except:
            # Default to perform filename crawl as a fallback
            self.filename_crawl = True

    @staticmethod
    def get_service_type():
        """Return the type of file service (Amazon)."""
        return "AmazonS3"

    def convert_file(self, item):
        """Convert the file details into a CazFile."""
        return CazFile(item.key,
                       os.path.basename(item.key),
                       None,
                       md5=item.e_tag.strip('"'),
                       path=item.key)

    def _find_object_by_lambda(self, bucket, func, find_one=False):
        """Crawl the contents of a bucket to find an object that passes the supplied function.

        Args:
            bucket (S3 Bucket): Reference to the S3 bucket used as the crawl root.
            func   (Lambda func): Comparison method that returns bool flag to include the object.
            find_one (bool): <Optional> Exit the processing loop after finding the first result.
        """
        matches = []
        for obj in bucket.objects.all():
            if func(obj):
                matches.append(self.convert_file(obj))
                if find_one:
                    # Exit out after first match
                    break

        return matches

    def _find_object_by_etag(self, bucket, tag=None, alt_tag=None, find_one=False):
        """Crawl the contents of a bucket to find the object with a specific tag."""
        if not tag and not alt_tag:
            raise ValueError("No valid search tag specified.")

        def find_by_tag(obj):
            etag = obj.e_tag.strip('"')
            return (tag and etag == tag) or (alt_tag and etag == alt_tag)

        return self._find_object_by_lambda(bucket, find_by_tag, find_one=find_one)

    def _find_object_by_name_wildcard(self, bucket, name, find_one=True):
        if not name:
            raise ValueError("No valid wildcard name specified.")

        def find_by_contains_name(obj):
            # S3 object names will contain the full path as the key
            # The easiest comparison is look for any match in a file path
            return name in obj.key

        return self._find_object_by_lambda(bucket, find_by_contains_name, find_one=find_one)

    def find_file(self, name=None, md5=None, sha1=None):
        """Find one or more files using the name and/or hash in the Amazon cloud service."""
        matches = []
        # AWS uses lowercase hash values
        if md5:
            md5 = md5.lower()
        if sha1:
            sha1 = sha1.lower()

        for b in self.buckets:
            s3_bucket = self.client.Bucket(b)
            if name:
                try:
                    obj = s3_bucket.Object(name)
                    obj.load()  # Pull the object summary details
                    matches.append(self.convert_file(obj))
                except botocore.exceptions.ClientError as e:
                    # 404 indicates not found
                    if e.response['Error']['Code'] != "404":
                        raise e
                    elif self.filename_crawl:
                        # Try to find a match by crawl
                        matches.extend(self._find_object_by_name_wildcard(s3_bucket, name))

            if md5 or sha1:
                logger.debug("Checking for hash {} and {}".format(md5, sha1))
                matches.extend(self._find_object_by_etag(s3_bucket, tag=md5, alt_tag=sha1))

        return matches

    def scan_files(self, temp_dir, expressions):
        """
        Scan all files for any content matches.

        Args:
            expressions (CazRegExp[]) List of regular expressions for content comparison
        """
        matches = []
        # Walk through the object and download files
        for b in self.buckets:
            s3_bucket = self.client.Bucket(b)
            for obj_sum in s3_bucket.objects.all():
                obj = self.client.Object(obj_sum.bucket_name, obj_sum.key)
                if obj.content_type == "binary/octet-stream":
                    # Skip folders
                    continue
                f_path = create_temp_name(temp_dir, obj_sum.key)
                logger.debug("Processing file {}...{}".format(obj_sum.key, f_path))
                obj.download_file(f_path)
                try:
                    matches.extend(search_content(f_path, expressions))
                except Exception as ex:
                    logger.error("Unable to parse content in file {}. {}".format(obj_sum.key, ex))

                try:
                    os.remove(f_path)
                except Exception as ex:
                    logger.error("Unable to clean up temprary file {}. {}".format(f_path, ex))

        return matches

    def get_file(self, name=None, md5=None, sha1=None):
        """Get a file from Amazon using the name or hashes."""
        raise NotImplementedError


# Register our handler
fileServiceInterface.register(amazonS3Handler)
