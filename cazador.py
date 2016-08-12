"""
Cazador file/cloud service investigator.

Cazador is an open source and freely available tool that allows users to quickly determine
if sensitive files are located within cloud environments.
"""

import os
import sys
import logging
from logging.config import fileConfig
import getopt
import pkgutil
import importlib
import configparser as ConfigParser

modulepath = os.path.realpath(os.path.dirname(__file__))
fileConfig(os.path.join(modulepath, 'logging.conf'), disable_existing_loggers=False)
logger = logging.getLogger("cazador")

_config = ConfigParser.RawConfigParser()

# Import all file services
import services
for _, name, _ in pkgutil.iter_modules([os.path.dirname(services.__file__)]):
    try:
        importlib.import_module('services.' + name)
    except Exception as ex:
        logger.error("Failed to import {}: {}".format(name, ex))

from fileservice import fileServiceInterface

# Register all service handlers with the file service interface and ensure
# they implement the necessary methods.
knownServices = fileServiceInterface.__subclasses__()
for srv in knownServices:
    logging.debug("Found service {} for {}".format(str(srv), srv.get_service_type()))


# TODO - Check if we want explicit constructor args or keyword
def get_service(fs_type, init_args):
    """
    Construct a file service object based on the type requested.

    Args:
        fs_type (string): Type of service to create
        kwargs: Keyword args to pass to the constructor

    Returns:
        fileServiceInterface: A instance handler for the file service.
    """
    for srv in knownServices:
        if srv.get_service_type().lower() == fs_type.lower():
            try:
                res = srv(init_args)
            except Exception as ex:
                logger.error("Failed to create service instance: {}".format(ex))
                raise

            return res

    raise ValueError("Unsupported file service type: {}".format(fs_type))


def print_known_services():
    """Print helper for known service list."""
    print("Known services:")
    for srv in knownServices:
        print("    {}".format(srv.get_service_type().lower()))


def print_help():
    """Print command line tool help."""
    print("""Cazador command line tool.
cazador.py -c <Config file>

    -s, --service= Cloud/File service type to search through.
                  !!! This must have a matching segment in the configuration document
    -c, --config= <Optional> File path to the configuration document for file/cloud service.
                  Default: [Current Directory]/cloud.conf""")
    print_known_services()

if __name__ == "__main__":
    argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argv,
                                   "hc:",
                                   ["config="])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)

    config_path = "cloud.conf"
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_help()
            sys.exit()
        elif opt in ("-s", "--service"):
            service_type = arg
        elif opt in ("-c", "--config"):
            config_path = arg

    if not service_type:
        logger.error("Unable to complete operation. No valid service type was specified.")
        print_help()
        sys.exit(2)

    _config.read(config_path)

    # Create a service instance
    service = get_service(service_type, _config[service_type])

    # TODO - Remove this test code !!!!
    f = "Krevshare_Myastan.txt"
    # Try name
    try:
        res = service.find_file(name=f)
        print(res)
    except Exception as ex:
        logger.error("Unexpected error finding file {}: {}".format(f, ex))

    # Try MD5
    f = "cfb19046b0d9b49e16918d0e2f7fce77"
    try:
        res = service.find_file(md5=f)
        print(res)
    except Exception as ex:
        logger.error("Unexpected error finding file {}: {}".format(f, ex))

    # Try a sha1
    f = "FF4B54F2903E3150BC3758F2FB83D153901D89B5"
    try:
        res = service.find_file(sha1=f)
        print(res)
    except Exception as ex:
        logger.error("Unexpected error finding file {}: {}".format(f, ex))
