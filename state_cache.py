import time

from configobj import ConfigObj

import config
import paths

_CURSOR_FROM_LAST_RUN_KEY = "cursor_from_last_run"
_TIME_FROM_LAST_RUN_KEY = "time_from_last_run"
_EXCLUDED_FOLDER_PATHS_FROM_LAST_RUN_KEY = "excluded_folder_paths_from_last_run"

_DEFAULTS = {
    _CURSOR_FROM_LAST_RUN_KEY: "",
    _TIME_FROM_LAST_RUN_KEY: 0.0,
    _EXCLUDED_FOLDER_PATHS_FROM_LAST_RUN_KEY: [],
}

_state_cache_file = paths.join(paths.cache_folder, config.APP_NAME + "_last_state")


def _load_last_run_state() -> ConfigObj:
    """Loads the state from the last run, initializing if it doesn't exist."""
    cache_tmp = ConfigObj(_state_cache_file, encoding="utf-8")
    for key, value in _DEFAULTS.items():
        if key not in cache_tmp:
            cache_tmp[key] = value
    cache_tmp[_TIME_FROM_LAST_RUN_KEY] = float(cache_tmp[_TIME_FROM_LAST_RUN_KEY])
    return cache_tmp


def store_state(cursor: str):
    """Stores the current state to the cache file."""
    cached_tmp = ConfigObj(_state_cache_file)
    cached_tmp[_CURSOR_FROM_LAST_RUN_KEY] = cursor
    cached_tmp[_TIME_FROM_LAST_RUN_KEY] = time.time()
    cached_tmp[_EXCLUDED_FOLDER_PATHS_FROM_LAST_RUN_KEY] = list(
        config.excluded_folder_paths_set
    )
    cached_tmp.write()


def excluded_folders_changed() -> bool:
    """Checks if the excluded folders have changed since the last run."""
    return (
        set(_state_last_run[_EXCLUDED_FOLDER_PATHS_FROM_LAST_RUN_KEY])
        != config.excluded_folder_paths_set
    )


_state_last_run = _load_last_run_state()

time_last_run = _state_last_run[_TIME_FROM_LAST_RUN_KEY]
cursor_from_last_run = _state_last_run[_CURSOR_FROM_LAST_RUN_KEY]
