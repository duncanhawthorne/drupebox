#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

from configobj import ConfigObj

from config import excluded_folder_paths, APP_NAME
from paths import path_exists, path_join
from utils import drupebox_cache_folder


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


_drupebox_cache_last_state_path = path_join(
    drupebox_cache_folder, APP_NAME + "_last_state"
)

state_last_run = _load_last_run_state()
time_last_run = state_last_run["time_from_last_run"]
