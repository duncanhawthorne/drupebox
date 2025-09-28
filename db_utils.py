#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time
from datetime import timezone

import dropbox
from send2trash import send2trash

from config import (
    config,
    config_ok_to_delete,
    get_remote_file_path,
    get_local_file_path,
    config_file_size_ok,
)
from log import note, alert, fyi
from paths import system_slash, get_containing_folder_path, db
from state_cache import state_last_run
from utils import is_server_connection_stale

"""
Variables in the following formats
remote_file_path -> dropbox format
remote_folder_path -> dropbox format (for the avoidance of doubt, no trailing slash)
local_file_path -> posix format, no trailing slash
local_folder_path -> posix format, no trailing slash
"""


def upload(local_file_path, remote_file_path):
    if config_file_size_ok(local_file_path):
        print("upload", remote_file_path)
        with open(local_file_path, "rb") as f:
            remote_file = _db_client.files_upload(
                f.read(),
                remote_file_path,
                mute=True,
                mode=dropbox.files.WriteMode("overwrite", None),
            )
        fix_local_time(remote_file, remote_file_path)
    else:
        note("File above max size, ignoring: " + remote_file_path)


def create_remote_folder(remote_file_path):
    print("create", remote_file_path)
    _db_client.files_create_folder(remote_file_path)


def create_local_folder(remote_file_path, local_file_path):
    print("create", remote_file_path)
    os.makedirs(local_file_path, exist_ok=True)


def download_file(remote_file_path, local_file_path):
    print("downld", remote_file_path)
    if os.path.exists(local_file_path):
        _delete_real(local_file_path)
    remote_file = _db_client.files_download_to_file(local_file_path, remote_file_path)
    fix_local_time(remote_file, remote_file_path)


def local_delete(local_file_path):
    remote_file_path = get_remote_file_path(local_file_path)
    assert config_ok_to_delete()  # as already checked this before calling local_delete
    alert(remote_file_path)
    _delete_real(local_file_path)


def _delete_real(local_file_path):
    # deleting local files uses send2trash so no files are permanently deleted locally
    send2trash(system_slash(local_file_path))


def remote_delete(local_file_path):
    remote_file_path = get_remote_file_path(local_file_path)
    alert(remote_file_path)
    try:
        _db_client.files_delete(remote_file_path)
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


def is_file(remote_item):
    return not isinstance(remote_item, dropbox.files.FolderMetadata)


def local_modified_time(local_file_path):
    return os.path.getmtime(local_file_path)


def remote_modified_time(remote_item):
    db_naive_time = remote_item.client_modified
    db_utc_time = db_naive_time.replace(tzinfo=timezone.utc)
    return db_utc_time.timestamp()


def fix_local_time(remote_file, remote_file_path):
    note("Fix local time for file")
    file_modified_time = remote_modified_time(remote_file)
    local_file_path = get_local_file_path(remote_file_path)
    os.utime(
        local_file_path,
        (
            int(file_modified_time),
            int(file_modified_time),
        ),
    )


def get_remote_folder(remote_folder_path):
    return [
        element
        for element in _get_all_remote_files()
        if db(get_containing_folder_path(element.path_display)) == remote_folder_path
    ]


def _get_all_remote_files_real():
    return _db_client.files_list_folder("", recursive=True).entries


_CACHE_TIME_KEY = "checked_time"
_CACHE_DATA_KEY = "data"


_all_remote_files_cache = {_CACHE_TIME_KEY: 0.0, _CACHE_DATA_KEY: []}


def _get_all_remote_files():
    if is_server_connection_stale(_all_remote_files_cache[_CACHE_TIME_KEY]):
        if _all_remote_files_cache[_CACHE_TIME_KEY] != 0:
            note("Last checked in with server over 60 seconds ago, refreshing")
        else:
            fyi("Scanning for files on Dropbox")
        _all_remote_files_cache[_CACHE_DATA_KEY] = _get_all_remote_files_real()
        _all_remote_files_cache[_CACHE_TIME_KEY] = time.time()
    return _all_remote_files_cache[_CACHE_DATA_KEY]


def item_not_found_at_remote(remote_folder, remote_file_path):
    for remote_item in remote_folder:
        if remote_item.path_display == remote_file_path:
            return False
    return True


def determine_remotely_deleted_files():
    cursor_last_run = state_last_run["cursor_from_last_run"]
    fyi("Scanning for any remotely deleted files since last Drupebox run")
    deleted_files = []
    if cursor_last_run != "":
        deltas = _db_client.files_list_folder_continue(cursor_last_run).entries
        for delta in deltas:
            if isinstance(delta, dropbox.files.DeletedMetadata):
                deleted_files.append(delta.path_display)
    if deleted_files:  # test not empty
        note("The following files were deleted on Dropbox since last run")
        for deleted_file in deleted_files:
            note(deleted_file)
    return deleted_files


def get_latest_db_state():
    return _db_client.files_list_folder_get_latest_cursor("", recursive=True).cursor


_db_client = dropbox.Dropbox(
    app_key=config["app_key"], oauth2_refresh_token=config["refresh_token"]
)
_get_all_remote_files()
