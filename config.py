#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from configobj import ConfigObj

from auth import dropbox_authorize
from log import note, fyi_ignore
from paths import (
    unix_slash,
    path_join,
    home,
    add_trailing_slash,
    path_exists,
    db,
)

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
APP_KEY = "1skff241na3x0at"
MAX_FILE_SIZE = 100000000


def _make_new_config_file(config_filename):
    config_tmp = ConfigObj()
    config_tmp.filename = config_filename

    config_tmp["app_key"] = APP_KEY
    config_tmp["refresh_token"] = dropbox_authorize(config_tmp["app_key"]).refresh_token

    default_path = path_join(home, "Dropbox")
    user_path_tmp = unix_slash(
        input(f"Enter dropbox local path (or press enter for {default_path}/) ").strip()
    )
    user_path_tmp = user_path_tmp or default_path
    user_path_tmp = add_trailing_slash(user_path_tmp)
    config_tmp["dropbox_local_path"] = user_path_tmp

    os.makedirs(config_tmp["dropbox_local_path"], exist_ok=True)
    config_tmp["max_file_size"] = MAX_FILE_SIZE
    config_tmp["excluded_folder_paths"] = [
        "/home/pi/SUPER_SECRET_LOCATION_1/",
        "/home/pi/SUPER SECRET LOCATION 2/",
    ]
    config_tmp["really_delete_local_files"] = False
    config_tmp.write()


def _sanitize_config(config_tmp):
    made_changes = False
    # format dropbox local path with forward slashes on all platforms and end with forward slash to ensure prefix-free
    original_dropbox_path = config_tmp["dropbox_local_path"]
    sanitized_dropbox_path = add_trailing_slash(original_dropbox_path)
    if original_dropbox_path != sanitized_dropbox_path:
        config_tmp["dropbox_local_path"] = sanitized_dropbox_path
        print("sanitized dropbox path")
        made_changes = True

    # format excluded paths with forward slashes on all platforms and end with forward slash to ensure prefix-free
    original_excluded_paths = config_tmp.get("excluded_folder_paths", [])
    sanitized_excluded_paths = [add_trailing_slash(p) for p in original_excluded_paths]
    if original_excluded_paths != sanitized_excluded_paths:
        config_tmp["excluded_folder_paths"] = sanitized_excluded_paths
        print("sanitized excluded paths")
        made_changes = True

    if made_changes:
        config_tmp.write()


def _get_config_real():
    config_dir = path_join(home, ".config")
    os.makedirs(config_dir, exist_ok=True)
    config_filename = path_join(config_dir, APP_NAME)
    if not path_exists(config_filename):
        # First time only
        _make_new_config_file(config_filename)

    config_tmp = ConfigObj(config_filename)

    _sanitize_config(config_tmp)

    return config_tmp


@cache
def _get_config():
    # uses cache decorator, so after first call, just returns cache of last call
    return _get_config_real()


def config_ok_to_delete():
    ok_to_delete = config.as_bool("really_delete_local_files")
    if not ok_to_delete:
        note("Drupebox not set to delete local files, so force reupload local file")
    return ok_to_delete


def _is_excluded_folder(local_folder_path):
    # forward slash at end of path ensures prefix-free
    local_folder_path_with_slash = add_trailing_slash(local_folder_path)
    remote_file_path = get_remote_file_path(local_folder_path_with_slash)
    for excluded_folder_path in excluded_folder_paths:
        if local_folder_path_with_slash.startswith(excluded_folder_path):
            print("exc", remote_file_path)
            return True
    return False


def skip(local_file_path):
    local_item = local_file_path.rstrip("/").split("/")[-1]  # rstrip for safety only
    for prefix in [".fuse_hidden"]:
        if local_item.startswith(prefix):
            fyi_ignore(prefix + " files")
            return True
    for suffix in [".pyc", "__pycache__", ".git"]:
        if local_item.endswith(suffix):
            fyi_ignore(suffix + " files")
            return True
    if local_item in [".DS_Store", "._.DS_Store", "DG1__DS_DIR_HDR", "DG1__DS_VOL_HDR"]:
        fyi_ignore(local_item)
        return True
    if _is_excluded_folder(local_file_path):
        return True
    return False


def get_remote_file_path(local_file_path):
    return db(local_file_path[len(dropbox_local_path) :])


def get_local_file_path(remote_file_path):
    return path_join(dropbox_local_path, remote_file_path)


config = _get_config()
dropbox_local_path = config["dropbox_local_path"]
excluded_folder_paths = config["excluded_folder_paths"]
