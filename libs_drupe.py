#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from datetime import datetime, timezone

import os
import dropbox
from send2trash import send2trash

from cache import load_last_state
from config import (
    config,
    config_ok_to_delete,
    dropbox_local_path,
    excluded_folder_paths,
)
from local_tree import load_tree
from log import note, alert, fyi_ignore, fyi
from paths import (
    system_slash,
    get_remote_file_path_of_local_file_path,
    path_join,
    add_trailing_slash,
)

"""
Variables in the following formats
remote_file_path -> dropbox format
remote_folder_path -> dropbox format (for the avoidance of doubt, no trailing slash)
local_file_path -> posix format, no trailing slash
local_folder_path -> posix format, no trailing slash
"""


def upload(local_file_path, remote_file_path):
    if os.path.getsize(local_file_path) < int(config["max_file_size"]):
        print("uuu", remote_file_path)
        with open(local_file_path, "rb") as f:
            remote_file = db_client.files_upload(
                f.read(),
                remote_file_path,
                mute=True,
                mode=dropbox.files.WriteMode("overwrite", None),
            )
        fix_local_time(remote_file, remote_file_path)
    else:
        note("File above max size, ignoring: " + remote_file_path)


def create_remote_folder(remote_file_path):
    print("ccc", remote_file_path)
    db_client.files_create_folder(remote_file_path)


def create_local_folder(remote_file_path, local_file_path):
    print("ccc", remote_file_path)
    os.makedirs(local_file_path, exist_ok=True)


def download_file(remote_file_path, local_file_path):
    print("ddd", remote_file_path)
    if os.path.exists(local_file_path):
        send2trash(
            system_slash(local_file_path)
        )  # so no files permanently deleted locally
    remote_file = db_client.files_download_to_file(local_file_path, remote_file_path)
    fix_local_time(remote_file, remote_file_path)


def local_delete(local_file_path):
    remote_file_path = get_remote_file_path_of_local_file_path(local_file_path)
    if (
        config_ok_to_delete()
    ):  # safety check that should be impossible to get to as this is checked before calling local_delete
        alert(remote_file_path)
        send2trash(system_slash(local_file_path))


def remote_delete(local_file_path):
    remote_file_path = get_remote_file_path_of_local_file_path(local_file_path)
    alert(remote_file_path)
    try:
        db_client.files_delete(remote_file_path)
    except dropbox.exceptions.ApiError as err:
        if (
            hasattr(err.error, "is_path_lookup")
            and err.error.is_path_lookup()
            and hasattr(err.error.get_path_lookup(), "is_not_found")
            and err.error.get_path_lookup().is_not_found()
        ):
            note("Tried to delete file on dropbox, but it was not there")
        else:
            note("Unexpected Dropbox API error on delete: " + str(err))


def readable_time(unix_time):
    return (
        datetime.fromtimestamp(float(unix_time), tz=timezone.utc).strftime(
            "%a, %d %b %Y %H:%M:%S +0000"
        )
        + " UTC"
    )


def is_file(remote_item):
    return not isinstance(remote_item, dropbox.files.FolderMetadata)


def local_modified_time(local_file_path):
    return os.path.getmtime(local_file_path)


def remote_modified_time(remote_item):
    db_naive_time = remote_item.client_modified
    a = db_naive_time
    db_utc_time = datetime(
        a.year, a.month, a.day, a.hour, a.minute, a.second, tzinfo=timezone.utc
    )
    return db_utc_time.timestamp()


def fix_local_time(remote_file, remote_file_path):
    note("Fix local time for file")
    file_modified_time = remote_modified_time(remote_file)
    local_file_path = path_join(dropbox_local_path, remote_file_path[1:])
    os.utime(
        local_file_path,
        (
            int(file_modified_time),
            int(file_modified_time),
        ),
    )


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


def get_remote_folder(remote_folder_path):
    return db_client.files_list_folder(remote_folder_path).entries


def local_item_not_found_at_remote(remote_folder, remote_file_path):
    for remote_item in remote_folder:
        if remote_item.path_display == remote_file_path:
            return False
    return True


def determine_remotely_deleted_files():
    cursor = last_state["cursor_from_last_run"]
    fyi("Scanning for any remotely deleted files since last Drupebox run")
    deleted_files = []
    if cursor != "":
        deltas = db_client.files_list_folder_continue(cursor).entries
        for delta in deltas:
            if isinstance(delta, dropbox.files.DeletedMetadata):
                deleted_files.append(delta.path_display)
    if deleted_files:  # test not empty
        note("The following files were deleted on Dropbox since last run")
        for deleted_file in deleted_files:
            note(deleted_file)
    return deleted_files


def get_last_state():
    return db_client.files_list_folder_get_latest_cursor("", recursive=True).cursor


file_tree_from_last_run = load_tree()
last_state = load_last_state()
time_from_last_run = last_state["time_from_last_run"]

db_client = dropbox.Dropbox(
    app_key=config["app_key"], oauth2_refresh_token=config["refresh_token"]
)
