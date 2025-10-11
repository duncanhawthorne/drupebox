#!/usr/bin/env python3
# -*- coding: utf-8 -*-

if __name__ == "__main__":
    # print early to give user feedback as imports can take a few seconds on raspberry pi
    print("Initiating libraries")

import os
import time

import db_utils as db
import local_tree
import log
import paths
import state_cache as state
from config import ok_to_delete_files, skip, get_local_file_path
from paths import dbfmt
from utils import readable_time, is_recent_last_run


def action_locally_deleted_files():
    """Syncs locally deleted files to Dropbox."""
    log.fyi("Syncing any locally deleted files since last Drupebox run")
    if state.excluded_folders_changed():
        log.note(
            "Changed list of excluded folder paths, skipping locally deleted files check"
        )
        return
    locally_deleted_files = local_tree.determine_locally_deleted_files()
    for locally_deleted_file in locally_deleted_files:
        log.note("Found locally deleted file, so delete on Dropbox")
        db.remote_delete(locally_deleted_file)


def action_folder(remote_folder_path):
    """Recursively syncs a folder between the local filesystem and Dropbox."""
    log.fyi(remote_folder_path)

    local_folder_path = get_local_file_path(remote_folder_path)

    remote_folder = db.get_remote_folder(remote_folder_path)

    # Go through remote items
    for remote_item in remote_folder:
        remote_file_path = remote_item.path_display
        local_file_path = get_local_file_path(remote_file_path)
        if skip(local_file_path):
            continue

        if (
            not paths.exists(local_file_path)
            or db.is_file(remote_item)
            and db.remote_modified_time(remote_item)
            > db.local_modified_time(local_file_path)
        ):
            if paths.exists(local_file_path):
                log.note("Found updated file on remote Dropbox, so download")
            else:
                log.note("Found new file on remote Dropbox, so download")

            if db.is_file(remote_item):
                db.download_file(remote_file_path, local_file_path)
            else:
                db.create_local_folder(remote_file_path, local_file_path)

        elif db.is_file(remote_item) and db.local_modified_time(
            local_file_path
        ) > db.remote_modified_time(remote_item):

            log.note("Local file has been updated, so upload")
            db.upload(local_file_path, remote_file_path)

    # Go through local items
    for local_item in os.listdir(local_folder_path):
        remote_file_path = dbfmt(paths.join(remote_folder_path, local_item))
        local_file_path = paths.join(local_folder_path, local_item)

        if skip(local_file_path):
            continue
        if db.item_not_found_at_remote(remote_folder, remote_file_path):
            if (
                state.time_last_run > db.local_modified_time(local_file_path)
                and is_recent_last_run(state.time_last_run)
                and remote_file_path in db.remotely_deleted_files()
                and ok_to_delete_files()
            ):
                log.note(
                    "Found local item that is deleted on remote Dropbox, so delete"
                )
                db.local_delete(local_file_path)
            else:
                if os.path.isdir(local_file_path):
                    log.note(
                        "Found local folder that isn't on remote Dropbox, so create"
                    )
                    db.create_remote_folder(remote_file_path)
                else:
                    log.note("Found local file that isn't on remote Dropbox, so upload")
                    db.upload(local_file_path, remote_file_path)

    # Go through sub-folders and repeat
    for sub_folder in os.listdir(local_folder_path):
        local_sub_folder_path = paths.join(local_folder_path, sub_folder)
        if os.path.isdir(local_sub_folder_path) and not skip(local_sub_folder_path):
            action_folder(dbfmt(paths.join(remote_folder_path, sub_folder)))


def main():
    """The main function of the Drupebox sync script."""
    print("Drupebox sync started at", readable_time(time.time()))
    action_locally_deleted_files()

    log.fyi("Syncing all other local and remote files changes")
    action_folder("")

    state.store_state(db.get_latest_state())
    local_tree.store_current_tree()
    print("Drupebox sync complete at", readable_time(time.time()))


if __name__ == "__main__":
    main()
