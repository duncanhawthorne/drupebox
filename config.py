#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

import dropbox
from configobj import ConfigObj

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
MAX_FILE_SIZE = 10000000


def dropbox_authorize(config_app_key):
    flow = dropbox.DropboxOAuth2FlowNoRedirect(
        config_app_key, use_pkce=True, token_access_type="offline"
    )
    authorize_url = flow.start()
    print(("1. Go to: " + authorize_url))
    print('2. Click "Allow" (you might have to log in first)')
    print("3. Copy the authorization code.")
    code = input("Enter the authorization code here: ").strip()
    return flow.finish(code)


def make_new_config_file(config_filename):
    config_tmp = ConfigObj()
    config_tmp.filename = config_filename

    config_tmp["app_key"] = APP_KEY
    config_tmp["refresh_token"] = dropbox_authorize(config_tmp["app_key"]).refresh_token

    config_tmp["dropbox_local_path"] = unix_slash(
        input(
            "Enter dropbox local path (or press enter for "
            + path_join(home, "Dropbox")
            + "/) "
        ).strip()
    )
    if config_tmp["dropbox_local_path"] == "":
        config_tmp["dropbox_local_path"] = path_join(home, "Dropbox")
    config_tmp["dropbox_local_path"] = add_trailing_slash(
        config_tmp["dropbox_local_path"]
    )
    if not path_exists(config_tmp["dropbox_local_path"]):
        os.makedirs(config_tmp["dropbox_local_path"])
    config_tmp["max_file_size"] = MAX_FILE_SIZE
    config_tmp["excluded_folder_paths"] = [
        "/home/pi/SUPER_SECRET_LOCATION_1/",
        "/home/pi/SUPER SECRET LOCATION 2/",
    ]
    config_tmp["really_delete_local_files"] = False
    config_tmp.write()


def sanitize_config(config_tmp):
    # format dropbox local path with forward slashes on all platforms and end with forward slash to ensure prefix-free
    if config_tmp["dropbox_local_path"] != add_trailing_slash(
        config_tmp["dropbox_local_path"]
    ):
        config_tmp["dropbox_local_path"] = add_trailing_slash(
            config_tmp["dropbox_local_path"]
        )
        config_tmp.write()

    # format excluded paths with forward slashes on all platforms and end with forward slash to ensure prefix-free
    excluded_folder_paths_sanitize = False
    for excluded_folder_path in config_tmp["excluded_folder_paths"]:
        if add_trailing_slash(excluded_folder_path) != excluded_folder_path:
            excluded_folder_paths_sanitize = True
            break

    if excluded_folder_paths_sanitize:
        excluded_folder_paths_tmp = []
        excluded_folder_paths_tmp[:] = [
            add_trailing_slash(excluded_folder_path)
            for excluded_folder_path in config_tmp["excluded_folder_paths"]
        ]
        config_tmp["excluded_folder_paths"] = excluded_folder_paths_tmp
        config_tmp.write()


def get_config_real():
    if not path_exists(path_join(home, ".config")):
        os.makedirs(path_join(home, ".config"))
    config_filename = path_join(home, ".config", APP_NAME)
    if not path_exists(config_filename):
        # First time only
        make_new_config_file(config_filename)

    config_tmp = ConfigObj(config_filename)

    sanitize_config(config_tmp)

    return config_tmp


def get_config():
    if get_config.cache is None:  # First run
        get_config.cache = get_config_real()
    return get_config.cache


get_config.cache = None


def config_ok_to_delete():
    if get_config()["really_delete_local_files"] != "True":
        note("Drupebox not set to delete local files, so force reupload local file")
        return False
    else:
        return True


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
    if is_excluded_folder(local_file_path):
        return True
    return False


def is_excluded_folder(local_folder_path):
    # forward slash at end of path ensures prefix-free
    local_folder_path_with_slash = add_trailing_slash(local_folder_path)
    remote_file_path = get_remote_file_path_of_local_file_path(
        local_folder_path_with_slash
    )
    for excluded_folder_path in excluded_folder_paths:
        if local_folder_path_with_slash.startswith(excluded_folder_path):
            print("exc", remote_file_path)
            return True
    return False


def get_remote_file_path_of_local_file_path(local_file_path):
    return db(local_file_path[len(dropbox_local_path) :])


config = get_config()
dropbox_local_path = config["dropbox_local_path"]
excluded_folder_paths = config["excluded_folder_paths"]
