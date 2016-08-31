"""
Cazador file/cloud service investigator.

Cazador is an open source and freely available tool that allows users to quickly determine
if sensitive files are located within cloud environments.

Created: 08/11/2016
Creator: Nathan Palmer
"""

import os
import sys
import traceback
import logging
from logging.config import fileConfig
import getopt
import pkgutil
import importlib
import configparser as ConfigParser
from cazobjects import CazRegEx

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
        logger.error(traceback.format_exc())
        logger.error("Failed to import {}: {}".format(name, ex))

from fileservice import fileServiceInterface

# Register all service handlers with the file service interface and ensure
# they implement the necessary methods.
knownServices = fileServiceInterface.__subclasses__()
for srv in knownServices:
    logging.debug("Found service {} for {}".format(str(srv), srv.get_service_type()))


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
cazador.py -c <Config file> -s <Service Type>

    -s, --service= Cloud/File service type to search through.
                  !!! This must have a matching segment in the configuration document
    -c, --config= <Optional> File path to the configuration document for file/cloud service.
                  Default: [Current Directory]/cloud.conf""")
    print_known_services()


def test_find_file(service):
    """Dev Test Method"""
    # TODO - Remove this test code !!!!
    f = "nate.png"
    # Try name
    try:
        res = service.find_file(name=f)
        for x in res:
            print(x)
    except Exception as ex:
        logger.error(traceback.format_exc())
        logger.error("Unexpected error finding file {}: {}".format(f, ex))

    f = "AWS_Serverless"
    # Try name
    try:
        res = service.find_file(name=f)
        for x in res:
            print(x)
    except Exception as ex:
        logger.error(traceback.format_exc())
        logger.error("Unexpected error finding file {}: {}".format(f, ex))

    # Try MD5
    f = "cfb19046b0d9b49e16918d0e2f7fce77"
    try:
        res = service.find_file(md5=f)
        for x in res:
            print(x)
    except Exception as ex:
        logger.error(traceback.format_exc())
        logger.error("Unexpected error finding file {}: {}".format(f, ex))

    # Try a sha1
    f = "FF4B54F2903E3150BC3758F2FB83D153901D89B5"
    try:
        res = service.find_file(sha1=f)
        for x in res:
            print(x)
    except Exception as ex:
        logger.error(traceback.format_exc())
        logger.error("Unexpected error finding file {}: {}".format(f, ex))

    # Try another sha1
    f = "5c279fb05a2bd6d4886844c05b214fc88f71abd4"
    try:
        res = service.find_file(sha1=f)
        for x in res:
            print(x)
    except Exception as ex:
        logger.error(traceback.format_exc())
        logger.error("Unexpected error finding file {}: {}".format(f, ex))


if __name__ == "__main__":
    argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argv,
                                   "hc:s:",
                                   ["config=", "service="])
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

    # Build a list of expression objects for performing content analysis
    regex_exps = []
    try:
        cfg_reg = _config["regex"]
        for x in cfg_reg:
            regex_exps.append(CazRegEx(x, cfg_reg[x]))
    except:
        # Ignore exceptions reading the configuration... it can be empty
        pass

    try:
        temp_dir = _config["scanner"]["temp_dir"]
    except:
        temp_dir = os.path.dirname(__file__)

    # TODO REMOVE THIS TEST CODE
    test_find = True
    if test_find:
        test_find_file(service)
        logger.info("")

    if len(regex_exps) > 0:
        logger.debug("Starting scan...")
        try:
            res = service.scan_files(temp_dir, regex_exps)
            logger.warn("{} scanned results found.".format(len(res)))
            count = 0
            for x in res:
                logger.warn("{}: {}".format(count, x))
                count += 1
        except Exception as ex:
            logger.error(traceback.format_exc())
            logger.error("Unexpected error scanning file contents. {}".format(ex))
    else:
        logger.info("Bypassing content scan. Not requested.")
