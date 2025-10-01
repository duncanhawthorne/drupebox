#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from functools import cache
from configobj import ConfigObj

import auth
import paths
from log import note, fyi_ignore

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
_APP_KEY = "1skff241na3x0at"
_MAX_FILE_SIZE = 100000000


def _determine_dropbox_folder_location():
    default_path = paths.join(paths.home, "Dropbox")
    user_path_tmp = paths.unix_slash(
        input(f"Enter dropbox local path (or press enter for {default_path}/) ").strip()
    )
    user_path_tmp = user_path_tmp or default_path
    user_path_tmp = paths.add_trailing_slash(user_path_tmp)
    os.makedirs(user_path_tmp, exist_ok=True)
    return user_path_tmp


def _make_new_config_file(config_filename):
    config_tmp = ConfigObj()
    config_tmp.filename = config_filename
    config_tmp["app_key"] = _APP_KEY
    config_tmp["refresh_token"] = auth.dropbox_authorize(config_tmp["app_key"])
    config_tmp["dropbox_local_path"] = _determine_dropbox_folder_location()
    config_tmp["max_file_size"] = _MAX_FILE_SIZE
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
    sanitized_dropbox_path = paths.add_trailing_slash(original_dropbox_path)
    if original_dropbox_path != sanitized_dropbox_path:
        config_tmp["dropbox_local_path"] = sanitized_dropbox_path
        note("sanitized dropbox path")
        made_changes = True

    # format excluded paths with forward slashes on all platforms and end with forward slash to ensure prefix-free
    original_excluded_paths = config_tmp.get("excluded_folder_paths", [])
    sanitized_excluded_paths = [
        paths.add_trailing_slash(p) for p in original_excluded_paths
    ]
    if original_excluded_paths != sanitized_excluded_paths:
        config_tmp["excluded_folder_paths"] = sanitized_excluded_paths
        note("sanitized excluded paths")
        made_changes = True

    if made_changes:
        config_tmp.write()


def _get_config_real():
    config_dir = paths.join(paths.home, ".config")
    os.makedirs(config_dir, exist_ok=True)
    config_filename = paths.join(config_dir, APP_NAME)
    if not paths.exists(config_filename):
        # First time only
        _make_new_config_file(config_filename)

    config_tmp = ConfigObj(config_filename)

    _sanitize_config(config_tmp)

    return config_tmp


@cache
def _get_config():
    # uses cache decorator, so after first call, just returns cache of last call
    return _get_config_real()


def ok_to_delete_files():
    ok_to_delete = _config.as_bool("really_delete_local_files")
    if not ok_to_delete:
        note("Drupebox not set to delete local files, so force reupload local file")
        # edit the drupebox config file really_delete_local_files if you want local files to be deleted
    return ok_to_delete


def _is_excluded_folder(local_folder_path):
    # forward slash at end of path ensures prefix-free
    local_folder_path_with_slash = paths.add_trailing_slash(local_folder_path)
    remote_file_path = get_remote_file_path(local_folder_path_with_slash)
    for excluded_folder_path in excluded_folder_paths:
        if local_folder_path_with_slash.startswith(excluded_folder_path):
            fyi_ignore(remote_file_path)
            return True
    return False


def skip(local_file_path):
    local_file_name = paths.get_file_name(local_file_path)
    for prefix in [".fuse_hidden"]:
        if local_file_name.startswith(prefix):
            fyi_ignore(prefix + " files")
            return True
    for suffix in [".pyc", "__pycache__", ".git"]:
        if local_file_name.endswith(suffix):
            fyi_ignore(suffix + " files")
            return True
    if local_file_name in [
        ".DS_Store",
        "._.DS_Store",
        "DG1__DS_DIR_HDR",
        "DG1__DS_VOL_HDR",
    ]:
        fyi_ignore(local_file_name)
        return True
    if _is_excluded_folder(local_file_path):
        return True
    return False


def file_size_ok(local_file_path):
    return os.path.getsize(local_file_path) < int(_config["max_file_size"])


def get_remote_file_path(local_file_path):
    return paths.db(local_file_path[len(dropbox_local_path) :])


def get_local_file_path(remote_file_path):
    return paths.join(dropbox_local_path, remote_file_path)


_config = _get_config()

dropbox_local_path = _config["dropbox_local_path"]
excluded_folder_paths = _config["excluded_folder_paths"]
app_key = _config["app_key"]
refresh_token = _config["refresh_token"]
