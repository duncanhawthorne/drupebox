#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

from configobj import ConfigObj

from config import excluded_folder_paths, APP_NAME
from paths import path_exists, path_join, cache_folder


def _load_last_run_state():
    cache_filename = _state_cache_file
    if not path_exists(cache_filename):
        cache_tmp = ConfigObj()
        cache_tmp.filename = cache_filename
        cache_tmp["cursor_from_last_run"] = ""
        cache_tmp["time_from_last_run"] = 0
        cache_tmp["excluded_folder_paths_from_last_run"] = []
    else:
        cache_tmp = ConfigObj(cache_filename)
        cache_tmp["time_from_last_run"] = float(cache_tmp["time_from_last_run"])
    return cache_tmp


def store_state(cursor):
    cache_filename = _state_cache_file
    cached_tmp = ConfigObj(cache_filename)
    cached_tmp["cursor_from_last_run"] = cursor
    cached_tmp["time_from_last_run"] = time.time()
    cached_tmp["excluded_folder_paths_from_last_run"] = excluded_folder_paths
    cached_tmp.write()


def excluded_folders_changed():
    return (
        not state_last_run["excluded_folder_paths_from_last_run"]
        == excluded_folder_paths
    )


_state_cache_file = path_join(cache_folder, APP_NAME + "_last_state")

state_last_run = _load_last_run_state()
time_last_run = state_last_run["time_from_last_run"]
