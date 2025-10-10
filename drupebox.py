#!/usr/bin/env python3
# -*- coding: utf-8 -*-

if __name__ == "__main__":
    # print early to give user feedback as imports can take a few seconds on raspberry pi
    print("Initiating libraries")

import os
import time

import local_tree
import log
import paths
import state_cache as state
from config import ok_to_delete_files, skip, get_local_file_path
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
    remotely_deleted_files,
    get_latest_db_state,
    item_not_found_at_remote,
)
from paths import db
from utils import readable_time, is_recent_last_run


def action_locally_deleted_files():
    log.fyi("Syncing any locally deleted files since last Drupebox run")
    if state.excluded_folders_changed():
        log.note(
            "Changed list of excluded folder paths, skipping locally deleted files check"
        )
        return
    locally_deleted_files = local_tree.determine_locally_deleted_files()
    for locally_deleted_file in locally_deleted_files:
        log.note("Found locally deleted file, so delete on Dropbox")
        remote_delete(locally_deleted_file)


def action_folder(remote_folder_path):
    log.fyi(remote_folder_path)

    local_folder_path = get_local_file_path(remote_folder_path)

    remote_folder = get_remote_folder(remote_folder_path)

    # Go through remote items
    for remote_item in remote_folder:
        remote_file_path = remote_item.path_display
        local_file_path = get_local_file_path(remote_file_path)
        if skip(local_file_path):
            continue

        if (
            not paths.exists(local_file_path)
            or is_file(remote_item)
            and remote_modified_time(remote_item) > local_modified_time(local_file_path)
        ):
            if paths.exists(local_file_path):
                log.note("Found updated file on remote Dropbox, so download")
            else:
                log.note("Found new file on remote Dropbox, so download")

            if is_file(remote_item):
                download_file(remote_file_path, local_file_path)
            else:
                create_local_folder(remote_file_path, local_file_path)

        elif is_file(remote_item) and local_modified_time(
            local_file_path
        ) > remote_modified_time(remote_item):

            log.note("Local file has been updated, so upload")
            upload(local_file_path, remote_file_path)

    # Go through local items
    for local_item in os.listdir(local_folder_path):
        remote_file_path = db(paths.join(remote_folder_path, local_item))
        local_file_path = paths.join(local_folder_path, local_item)

        if skip(local_file_path):
            continue
        if item_not_found_at_remote(remote_folder, remote_file_path):
            if (
                state.time_last_run > local_modified_time(local_file_path)
                and is_recent_last_run(state.time_last_run)
                and remote_file_path in remotely_deleted_files()
                and ok_to_delete_files()
            ):
                log.note(
                    "Found local item that is deleted on remote Dropbox, so delete"
                )
                local_delete(local_file_path)
            else:
                if os.path.isdir(local_file_path):
                    log.note(
                        "Found local folder that isn't on remote Dropbox, so create"
                    )
                    create_remote_folder(remote_file_path)
                else:
                    log.note("Found local file that isn't on remote Dropbox, so upload")
                    upload(local_file_path, remote_file_path)

    # Go through sub-folders and repeat
    for sub_folder in os.listdir(local_folder_path):
        local_sub_folder_path = paths.join(local_folder_path, sub_folder)
        if os.path.isdir(local_sub_folder_path) and not skip(local_sub_folder_path):
            action_folder(db(paths.join(remote_folder_path, sub_folder)))


def main():
    print("Drupebox sync started at", readable_time(time.time()))
    action_locally_deleted_files()

    log.fyi("Syncing all other local and remote files changes")
    action_folder("")

    state.store_state(get_latest_db_state())
    local_tree.store_current_tree()
    print("Drupebox sync complete at", readable_time(time.time()))


if __name__ == "__main__":
    main()
