#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import time

from configobj import ConfigObj

from config import excluded_folder_paths, APP_NAME
from paths import path_exists, add_trailing_slash, path_join, home


def _load_last_run_state():
    config_filename = _drupebox_cache_last_state_path
    if not path_exists(config_filename):
        config_tmp = ConfigObj()
        config_tmp.filename = config_filename
        config_tmp["cursor_from_last_run"] = ""
        config_tmp["time_from_last_run"] = 0
        config_tmp["excluded_folder_paths_from_last_run"] = []
    else:
        config_tmp = ConfigObj(config_filename)
        config_tmp["time_from_last_run"] = float(config_tmp["time_from_last_run"])
    return config_tmp


def store_state(cursor):
    config_filename = _drupebox_cache_last_state_path
    config_tmp = ConfigObj(config_filename)
    config_tmp["cursor_from_last_run"] = cursor
    config_tmp["time_from_last_run"] = time.time()
    config_tmp["excluded_folder_paths_from_last_run"] = excluded_folder_paths
    config_tmp.write()


def excluded_folders_changed():
    return (
        not state_last_run["excluded_folder_paths_from_last_run"]
        == excluded_folder_paths
    )


if sys.platform != "win32":
    _drupebox_cache = "/dev/shm/"
else:
    _drupebox_cache = add_trailing_slash(path_join(home, ".config"))

drupebox_cache_file_list_path = path_join(
    _drupebox_cache, APP_NAME + "_last_seen_files"
)
_drupebox_cache_last_state_path = path_join(_drupebox_cache, APP_NAME + "_last_state")

state_last_run = _load_last_run_state()
time_last_run = state_last_run["time_from_last_run"]
