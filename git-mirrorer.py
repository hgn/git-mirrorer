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

def repo_full_path(conf, repo_name):
    full_repo_name = "{}.git".format(repo_name)
    return os.path.join(conf.dst_path, full_repo_name)

def get_current_repo_dirs(conf, repo_conf):
    repos = dict()
    for name in os.listdir(conf.dst_path):
        full_path = os.path.join(conf.dst_path, name)
        if os.path.isdir(full_path):
            repos[full_path] = True
    return repos

def rm_outdated_repos(repos):
    """ if a repo is removed from the JSON configuration file it
        will be instantly removed from the cloned repository. This
        Will ensure a (manual) way to change to change a URL for a
        given repository """
    for repo_path, _ in repos.items():
        if not os.path.isdir(repo_path):
            log.error("repo not available, but should: {}".format(repo_path))
        else:
            log.warning("remove renamed/deleted repository: {}".format(repo_path))
            shutil.rmtree(repo_path)


def process_repo_list(conf, repo_conf):
    log.debug(pp.pformat(repo_conf))
    currently_cloned_repos = get_current_repo_dirs(conf, repo_conf)
    for repo_name, repo_data in repo_conf['repositories'].items():
        dst_path = repo_full_path(conf, repo_name)
        if os.path.isdir(dst_path):
            log.warning("update repository {}".format(repo_name))
            repo_pull(conf, dst_path)
            del currently_cloned_repos[dst_path]
        else:
            log.warning("clone new repository {}".format(repo_name))
            bare_clone_repo(conf, repo_data['url'], dst_path)
    rm_outdated_repos(currently_cloned_repos)


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
