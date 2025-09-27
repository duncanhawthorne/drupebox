#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import time

from config import config_ok_to_delete, skip, get_local_file_path
from db_utils import (
    remote_delete,
    get_remote_folder,
    is_file,
    remote_modified_time,
    local_modified_time,
    download_file,
    create_local_folder,
    upload,
    create_remote_folder,
    local_delete,
    determine_remotely_deleted_files,
    get_latest_db_state,
    item_not_found_at_remote,
)
from local_tree import (
    get_live_local_tree,
    store_tree,
    determine_locally_deleted_files,
    file_tree_from_last_run,
)
from log import note, fyi
from paths import path_exists, db, path_join
from state_cache import store_state, time_last_run, excluded_folders_changed
from utils import readable_time, is_server_connection_stale, is_recent_last_run


def action_locally_deleted_files():
    fyi("Syncing any locally deleted files since last Drupebox run")
    if excluded_folders_changed():
        note(
            "Changed list of excluded folder paths, skipping locally deleted files check"
        )
        return
    file_tree_now = get_live_local_tree()
    locally_deleted_files = determine_locally_deleted_files(
        file_tree_now, file_tree_from_last_run
    )
    for locally_deleted_file in locally_deleted_files:
        note("Found locally deleted file, so delete on Dropbox")
        remote_delete(locally_deleted_file)


def action_folder(remote_folder_path):
    fyi(remote_folder_path)

    local_folder_path = get_local_file_path(remote_folder_path)

    remote_folder = get_remote_folder(remote_folder_path)
    remote_folder_checked_time = time.time()

    # Go through remote items
    for remote_item in remote_folder:
        if is_server_connection_stale(remote_folder_checked_time):
            note("Last checked in with server over 60 seconds ago, refreshing")
            action_folder(remote_folder_path)
            return
        remote_file_path = remote_item.path_display
        local_file_path = get_local_file_path(remote_file_path)
        if skip(local_file_path):
            continue

        if (
            not path_exists(local_file_path)
            or is_file(remote_item)
            and remote_modified_time(remote_item) > local_modified_time(local_file_path)
        ):
            if path_exists(local_file_path):
                note("Found updated file on remote Dropbox, so download")
            else:
                note("Found new file on remote Dropbox, so download")

            if is_file(remote_item):
                download_file(remote_file_path, local_file_path)
            else:
                create_local_folder(remote_file_path, local_file_path)

        elif is_file(remote_item) and local_modified_time(
            local_file_path
        ) > remote_modified_time(remote_item):

            note("Local file has been updated, so upload")
            upload(local_file_path, remote_file_path)

    # Go through local items
    for local_item in os.listdir(local_folder_path):
        if is_server_connection_stale(remote_folder_checked_time):
            note("Last checked in with server over 60 seconds ago, refreshing")
            action_folder(remote_folder_path)
            return
        remote_file_path = db(path_join(remote_folder_path, local_item))
        local_file_path = path_join(local_folder_path, local_item)

        if skip(local_file_path):
            continue
        if item_not_found_at_remote(remote_folder, remote_file_path):
            if (
                time_last_run > local_modified_time(local_file_path)
                and is_recent_last_run(time_last_run)
                and remote_file_path in remotely_deleted_files
                and config_ok_to_delete()
            ):
                note("Found local item that is deleted on remote Dropbox, so delete")
                local_delete(local_file_path)
            else:
                if os.path.isdir(local_file_path):
                    note("Found local folder that isn't on remote Dropbox, so create")
                    create_remote_folder(remote_file_path)
                else:
                    note("Found local file that isn't on remote Dropbox, so upload")
                    upload(local_file_path, remote_file_path)

    # Go through sub-folders and repeat
    for sub_folder in os.listdir(local_folder_path):
        local_sub_folder_path = path_join(local_folder_path, sub_folder)
        if os.path.isdir(local_sub_folder_path) and not skip(local_sub_folder_path):
            action_folder(db(path_join(remote_folder_path, sub_folder)))


print("Drupebox sync started at", readable_time(time.time()))
remotely_deleted_files = determine_remotely_deleted_files()
action_locally_deleted_files()

fyi("Syncing all other local and remote files changes")
action_folder("")

store_state(get_latest_db_state())
store_tree(get_live_local_tree())
print("Drupebox sync complete at", readable_time(time.time()))
