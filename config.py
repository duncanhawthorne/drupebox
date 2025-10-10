#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from functools import cache

from configobj import ConfigObj

import auth
import log
import paths

APP_NAME = "drupebox"
# To create new app key:
# Go to https://www.dropbox.com/developers/apps
# Click "Create App"
# Click "Scoped access" and "App folder"
# Enter a name for your App and click Create app
# Go to the Permissions tab
# Check "files.content.write" and "files.content.read"
# Click "Submit"
# On the Settings tab, copy the App key
# Update the APP_KEY variable below to your App key
_APP_KEY_DEFAULT = "1skff241na3x0at"
_MAX_FILE_SIZE_DEFAULT = 100000000

_APP_KEY_KEY = "app_key"
_REFRESH_TOKEN_KEY = "refresh_token"
_DROPBOX_LOCAL_PATH_KEY = "dropbox_local_path"
_MAX_FILE_SIZE_KEY = "max_file_size"
_EXCLUDED_FOLDER_PATHS_KEY = "excluded_folder_paths"
_REALLY_DELETE_LOCAL_FILES_KEY = "really_delete_local_files"


def _determine_dropbox_folder_location():
    while True:
        try:
            default_path = paths.join(paths.home, "Dropbox")
            user_path_tmp = paths.unix_slash(
                input(
                    f"Enter dropbox local path (or press enter for {default_path}/) "
                ).strip()
            )
            user_path_tmp = user_path_tmp or default_path
            user_path_tmp = paths.add_trailing_slash(user_path_tmp)
            os.makedirs(user_path_tmp, exist_ok=True)
            return user_path_tmp
        except Exception as e:
            print(e)


def _make_new_config_file(config_filename):
    config_tmp = ConfigObj()
    config_tmp.filename = config_filename
    config_tmp.write()


def _initialize_config_file(config_tmp):
    # if properly configured config file, no action taken
    made_changes = False
    if _APP_KEY_KEY not in config_tmp:
        config_tmp[_APP_KEY_KEY] = _APP_KEY_DEFAULT
        made_changes = True
    if _REFRESH_TOKEN_KEY not in config_tmp:
        config_tmp[_REFRESH_TOKEN_KEY] = auth.dropbox_authorize(
            config_tmp[_APP_KEY_KEY]
        )
        made_changes = True
    if _DROPBOX_LOCAL_PATH_KEY not in config_tmp:
        config_tmp[_DROPBOX_LOCAL_PATH_KEY] = _determine_dropbox_folder_location()
        made_changes = True
    if _MAX_FILE_SIZE_KEY not in config_tmp:
        config_tmp[_MAX_FILE_SIZE_KEY] = _MAX_FILE_SIZE_DEFAULT
        made_changes = True
    if _EXCLUDED_FOLDER_PATHS_KEY not in config_tmp:
        config_tmp[_EXCLUDED_FOLDER_PATHS_KEY] = [
            "/home/pi/SUPER_SECRET_LOCATION_1/",
            "/home/pi/SUPER SECRET LOCATION 2/",
        ]
        made_changes = True
    if _REALLY_DELETE_LOCAL_FILES_KEY not in config_tmp:
        config_tmp[_REALLY_DELETE_LOCAL_FILES_KEY] = False
        made_changes = True

    if made_changes:
        log.note("Initialised config file")
        config_tmp.write()

    # fix types where read to incorrect types from config file
    config_tmp[_REALLY_DELETE_LOCAL_FILES_KEY] = config_tmp.as_bool(
        _REALLY_DELETE_LOCAL_FILES_KEY
    )
    config_tmp[_MAX_FILE_SIZE_KEY] = int(config_tmp[_MAX_FILE_SIZE_KEY])


def _sanitize_config(config_tmp):
    made_changes = False
    # format dropbox local path with forward slashes on all platforms and end with forward slash to ensure prefix-free
    original_dropbox_path = config_tmp[_DROPBOX_LOCAL_PATH_KEY]
    sanitized_dropbox_path = paths.add_trailing_slash(original_dropbox_path)
    if original_dropbox_path != sanitized_dropbox_path:
        config_tmp[_DROPBOX_LOCAL_PATH_KEY] = sanitized_dropbox_path
        log.note("Sanitized dropbox path")
        made_changes = True

    # format excluded paths with forward slashes on all platforms and end with forward slash to ensure prefix-free
    original_excluded_paths = config_tmp.get(_EXCLUDED_FOLDER_PATHS_KEY, [])
    sanitized_excluded_paths = [
        paths.add_trailing_slash(p) for p in original_excluded_paths
    ]
    if original_excluded_paths != sanitized_excluded_paths:
        config_tmp[_EXCLUDED_FOLDER_PATHS_KEY] = sanitized_excluded_paths
        log.note("Sanitized excluded paths")
        made_changes = True

    if made_changes:
        config_tmp.write()


def _get_config_real():
    config_dir = paths.join(paths.home, ".config")
    os.makedirs(config_dir, exist_ok=True)
    config_filename = paths.join(config_dir, APP_NAME)
    if not paths.exists(config_filename):
        _make_new_config_file(config_filename)

    config_tmp = ConfigObj(config_filename)
    _initialize_config_file(config_tmp)

    _sanitize_config(config_tmp)

    return config_tmp


@cache
def _get_config():
    # uses cache decorator, so after first call, just returns cache of last call
    return _get_config_real()


def ok_to_delete_files():
    ok_to_delete = _config[_REALLY_DELETE_LOCAL_FILES_KEY]
    if not ok_to_delete:
        log.note("Drupebox not set to delete local files, so force reupload local file")
        # edit the drupebox config file really_delete_local_files if you want local files to be deleted
    return ok_to_delete


def _is_excluded_folder(local_folder_path):
    # forward slash at end of path ensures prefix-free
    local_folder_path_with_slash = paths.add_trailing_slash(local_folder_path)
    return any(
        local_folder_path_with_slash.startswith(excluded_path)
        for excluded_path in excluded_folder_paths
    )


def skip(local_file_path):
    local_file_name = paths.get_file_name(local_file_path)
    if (
        any(local_file_name.startswith(prefix) for prefix in {".fuse_hidden"})
        or any(
            local_file_name.endswith(suffix)
            for suffix in {".pyc", "__pycache__", ".git"}
        )
        or local_file_name
        in {
            ".DS_Store",
            "._.DS_Store",
            "DG1__DS_DIR_HDR",
            "DG1__DS_VOL_HDR",
        }
        or _is_excluded_folder(local_file_path)
    ):
        log.fyi_ignore(local_file_path)
        return True
    else:
        return False


def file_size_ok(local_file_path):
    return os.path.getsize(local_file_path) < _config[_MAX_FILE_SIZE_KEY]


def get_remote_file_path(local_file_path):
    return paths.db(local_file_path[len(dropbox_local_path) :])


def get_local_file_path(remote_file_path):
    return paths.join(dropbox_local_path, remote_file_path)


_config = _get_config()

dropbox_local_path = _config[_DROPBOX_LOCAL_PATH_KEY]
excluded_folder_paths = _config[_EXCLUDED_FOLDER_PATHS_KEY]
app_key = _config[_APP_KEY_KEY]
refresh_token = _config[_REFRESH_TOKEN_KEY]
