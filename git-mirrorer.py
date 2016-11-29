#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import addict
import time
import sys
import os
import json
import datetime
import pprint
import subprocess
import logging
import argparse

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--configuration", help="configuration", type=str, default=None)
    parser.add_argument("-v", "--verbose", help="verbose", action='store_true', default=False)
    args = parser.parse_args()
    if not args.configuration:
        print("Configuration required, please specify a valid file path, exiting now")
        sys.exit(EXIT_FAILURE)
    return args


def load_configuration_file(args):
    with open(args.configuration) as json_data:
        return addict.Dict(json.load(json_data))


def init_global_behavior(args, conf):
    logger = logging.getLogger()
    if conf.loglevel:   
        logger.setLevel(logging.DEBUG)
    if args.verbose:
        logger.setLevel(logging.DEBUG)


def conf_init():
    args = parse_args()
    conf = load_configuration_file(args)
    init_global_behavior(args, conf)
    return conf


def main(conf):
    pass


if __name__ == '__main__':
    print("git-mirrorer, 2016")
    conf = conf_init()
    main(conf)
