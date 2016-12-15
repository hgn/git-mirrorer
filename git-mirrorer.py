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

def cmd_exec(cmd):
    log.debug("execute: \"{}\"".format(cmd))
    try:
        out = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT, shell=False)
    except subprocess.CalledProcessError:
        log.error("Failed to execute {}".format(cmd))
        return False
    lines = str(out, 'utf-8')
    for line in lines.splitlines(): log.error(line)
    return True

def build_prefix(prefix, name):
    if prefix:
        return "{}-{}".format(prefix, name)
    return name

def clone_mirror_list_repo(git_mirror_url, name=None, prefix=None, disable_proxy=False):
    out_dir = build_prefix(prefix, name)
    proxy = ""
    if disable_proxy:
        proxy = "-c http.proxy="
    cmd = "git {} clone -vv {} {}".format(proxy, git_mirror_url, out_dir)
    ok = cmd_exec(cmd)
    if not ok:
        return False, None
    return True, out_dir

def bare_clone_repo(url, name):
    cmd = "git clone --bare -vv {} {}".format(url, name)
    cmd_exec(cmd)

def repo_pull(bare_path):
    old_dir = os.getcwd()
    os.chdir(bare_path)
    cmd = "git fetch origin +refs/heads/*:refs/heads/* --prune"
    cmd_exec(cmd)
    os.chdir(old_dir)

def repo_full_path(prefix, repo_name):
    name = build_prefix(prefix, repo_name)
    full_repo_name = "{}.git".format(name)
    return os.path.join(conf.dst_path, full_repo_name)

def get_current_repo_dirs(dst_path):
    repos = dict()
    for name in os.listdir(dst_path):
        full_path = os.path.join(dst_path, name)
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

def change_description(orig_url, path):
    desc_path = os.path.join(path, "description")
    with open(desc_path, 'w+') as f:
        f.write(orig_url)

def process_repo_list(prefix, dst_path, repo_conf, ccr):
    log.debug(pp.pformat(repo_conf))
    for repo_name, repo_data in repo_conf['repositories'].items():
        dst_path = repo_full_path(prefix, repo_name)
        if os.path.isdir(dst_path):
            log.warning("update repository {}".format(repo_name))
            repo_pull(dst_path)
            del ccr[dst_path]
        else:
            log.warning("clone new repository {}".format(repo_name))
            bare_clone_repo(repo_data['url'], dst_path)
            change_description(repo_data['url'], dst_path)

def repo_processing(conf, prefix, git_mirror_url, ccr):
    log.error("process: prefix:{}, url:{}".format(prefix, git_mirror_url))
    ok, dirname = clone_mirror_list_repo(git_mirror_url, name="mirror-list", prefix=prefix, disable_proxy=True)
    if not ok: return False
    repo_conf_path = os.path.join(dirname, "git-mirror-list.json")
    if not os.path.isfile(repo_conf_path):
        msg = "mirror list *not* cloned or git-mirror-list.json not available here {}"
        log.critical(msg.format(repo_conf_path))
        sys.exit(EXIT_FAILURE)
    with open(repo_conf_path) as json_data:
        repo_conf = json.load(json_data)
        process_repo_list(prefix, conf.dst_path, repo_conf, ccr)
    shutil.rmtree(dirname)
    return True

def process_mirror_list(conf, mirror_repo_conf, ccr):
    for entry in mirror_repo_conf:
        url = entry['url']
        prefix = entry['prefix']
        responsible = entry['responsible']
        ok = repo_processing(conf, prefix, url, ccr)
        if not ok: return False
    return True

def process_mirror_register(conf, ccr):
    ok, mirror_path = clone_mirror_list_repo(conf.mirror_register_repo, name="register-list", disable_proxy=True)
    if not ok:
        return False
    filename = "git-mirror-register.json"
    mirror_conf_path = os.path.join(mirror_path, filename)
    if not os.path.isfile(mirror_conf_path):
        msg = "mirror list *not* cloned or {} not available here {}"
        log.critical(msg.format(filename, mirror_conf_path))
        sys.exit(EXIT_FAILURE)
    with open(mirror_conf_path) as json_data:
        mirror_repo_conf = json.load(json_data)
        ok = process_mirror_list(conf, mirror_repo_conf, ccr)
        if not ok: return False
    return True

def do(conf):
    ccr = get_current_repo_dirs(conf.dst_path)
    ok = process_mirror_register(conf, ccr)
    if ok:
        rm_outdated_repos(ccr)

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
        try:
            return addict.Dict(json.load(json_data))
        except json.decoder.JSONDecodeError:
            log.error("Configuration file seems corrupt: {}".format(args.configuration))
            sys.exit(EXIT_FAILURE)


def init_global_behavior(args, conf):
    if conf.loglevel:
        log.setLevel(conf.loglevel)
    if args.verbose:
        print("DEBUG mode")
        log.setLevel(logging.DEBUG)

def conf_check(conf):
    if not conf.mirror_register_repo:
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
