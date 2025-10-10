#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

from configobj import ConfigObj

import config
import paths

_CURSOR_FROM_LAST_RUN_KEY = "cursor_from_last_run"
_TIME_FROM_LAST_RUN_KEY = "time_from_last_run"
_EXCLUDED_FOLDER_PATHS_FROM_LAST_RUN_KEY = "excluded_folder_paths_from_last_run"


def _load_last_run_state():
    cache_filename = _state_cache_file
    if not paths.exists(cache_filename):
        cache_tmp = ConfigObj()
        cache_tmp.filename = cache_filename
        cache_tmp[_CURSOR_FROM_LAST_RUN_KEY] = ""
        cache_tmp[_TIME_FROM_LAST_RUN_KEY] = 0.0
        cache_tmp[_EXCLUDED_FOLDER_PATHS_FROM_LAST_RUN_KEY] = []
    else:
        cache_tmp = ConfigObj(cache_filename)
        cache_tmp[_TIME_FROM_LAST_RUN_KEY] = float(cache_tmp[_TIME_FROM_LAST_RUN_KEY])
    return cache_tmp


def store_state(cursor):
    cache_filename = _state_cache_file
    cached_tmp = ConfigObj(cache_filename)
    cached_tmp[_CURSOR_FROM_LAST_RUN_KEY] = cursor
    cached_tmp[_TIME_FROM_LAST_RUN_KEY] = time.time()
    cached_tmp[_EXCLUDED_FOLDER_PATHS_FROM_LAST_RUN_KEY] = config.excluded_folder_paths
    cached_tmp.write()


def excluded_folders_changed():
    return (
        not _state_last_run[_EXCLUDED_FOLDER_PATHS_FROM_LAST_RUN_KEY]
        == config.excluded_folder_paths
    )


_state_cache_file = paths.join(paths.cache_folder, config.APP_NAME + "_last_state")
_state_last_run = _load_last_run_state()

time_last_run = _state_last_run[_TIME_FROM_LAST_RUN_KEY]
cursor_from_last_run = _state_last_run[_CURSOR_FROM_LAST_RUN_KEY]
