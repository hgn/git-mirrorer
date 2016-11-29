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
import tempfile
import shutil

EXIT_SUCCESS = 0
EXIT_FAILURE = 1

log = logging.getLogger()
pp = pprint.PrettyPrinter(indent=2)

def cmd_exec(conf, cmd):
    out = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT, shell=False)
    lines = str(out, 'utf-8')
    for line in lines.splitlines(): log.error(line)

def clone_mirror_list_repo(conf):
    out_dir = "mirror-list"
    cmd = "git clone -vv {} {}".format(conf.mirror_list_repo_url, out_dir)
    cmd_exec(conf, cmd)
    return out_dir

def bare_clone_repo(conf, url, name):
    cmd = "git clone --bare -vv {} {}".format(url, name)
    cmd_exec(conf, cmd)

def repo_pull(conf, bare_path):
    old_dir = os.getcwd()
    os.chdir(bare_path)
    cmd = "git fetch origin +refs/heads/*:refs/heads/* --prune"
    cmd_exec(conf, cmd)
    os.chdir(old_dir)

def process_repo_list(conf, repo_conf):
    log.debug(pp.pformat(repo_conf))
    for repo_name, repo_data in repo_conf['repositories'].items():
        full_repo_name = "{}.git".format(repo_name)
        dst_path = os.path.join(conf.dst_path, full_repo_name)
        if os.path.isdir(dst_path):
            repo_pull(conf, dst_path)
        else:
            log.warning("process {}".format(repo_name))
            bare_clone_repo(conf, repo_data['url'], dst_path)
            #shutil.move(repo_name, target)


def do(conf):
    dirname = clone_mirror_list_repo(conf)
    repo_conf_path = os.path.join(dirname, "git-mirror-list.json")
    if not os.path.isfile(repo_conf_path):
        log.critical("mirror list *not* cloned, not available here {}".format(repo_conf_path))
        sys.exit(EXIT_FAILURE)
    with open(repo_conf_path) as json_data:
        repo_conf = json.load(json_data)
    process_repo_list(conf, repo_conf)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--configuration",
                        help="configuration", type=str, default=None)
    parser.add_argument("-v", "--verbose", help="verbose",
                        action='store_true', default=False)
    args = parser.parse_args()
    if not args.configuration:
        print("Configuration required, please specify a valid "
              "file path, exiting now")
        sys.exit(EXIT_FAILURE)
    return args


def load_configuration_file(args):
    with open(args.configuration) as json_data:
        return addict.Dict(json.load(json_data))


def init_global_behavior(args, conf):
    if conf.loglevel:
        log.setLevel(conf.loglevel)
    if args.verbose:
        print("DEBUG mode")
        log.setLevel(logging.DEBUG)

def conf_check(conf):
    if not conf.mirror_list_repo_url:
        log.error("no mirror repository specified in configuration file")
        sys.exit(EXIT_FAILURE)
    if not os.path.isdir(conf.dst_path):
        os.makedirs(conf.dst_path)

def conf_init():
    args = parse_args()
    conf = load_configuration_file(args)
    init_global_behavior(args, conf)
    conf_check(conf)
    return conf


def main(conf):
    # create tmp environmet
    start_dir = os.getcwd()
    tmppath = tempfile.mkdtemp()
    os.chdir(tmppath)
    try:
        do(conf)
    finally:
        # cleanup the environmet
        os.chdir(start_dir)
        shutil.rmtree(tmppath)


if __name__ == '__main__':
    conf = conf_init()
    log.error("git-mirrorer, 2016")
    main(conf)
