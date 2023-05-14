#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from libs_drupe import *


def action_locally_deleted_files():
    fyi("Syncing any locally deleted files since last Drupebox run")
    file_tree_now = get_live_tree()
    locally_deleted_files = determine_locally_deleted_files(
        file_tree_now, file_tree_from_last_run
    )
    for locally_deleted_file in locally_deleted_files:
        note("Found locally deleted file, so delete on Dropbox")
        remote_delete(locally_deleted_file)


def action_folder(remote_folder_path):
    fyi(remote_folder_path)

    local_folder_path = dropbox_local_path + remote_folder_path[1:] + "/"
    if is_excluded_folder(local_folder_path):
        return

    remote_folder = db_client.files_list_folder(remote_folder_path).entries
    remote_folder_checked_time = time.time()

    # Go through remote items
    for remote_item in remote_folder:
        if time.time() > remote_folder_checked_time + 60:
            note("Last checked in with server over 60 seconds ago, refreshing")
            action_folder(remote_folder_path)
            return
        remote_file_path = remote_item.path_display
        local_file_path = path_join(dropbox_local_path, remote_file_path[1:])
        if not is_file(remote_item):
            local_file_path = add_trailing_slash(local_file_path)
        if skip(local_file_path) or is_excluded_folder(local_file_path):
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

            if is_file(remote_item):
                note("Local file has been updated, so upload")
                upload(local_file_path, remote_file_path)
            else:
                "Modification time on a folder does not matter - no action"

    # Go throgh local items
    for local_item in os.listdir(local_folder_path):
        if time.time() > remote_folder_checked_time + 60:
            note("Last checked in with server over 60 seconds ago, refreshing")
            action_folder(remote_folder_path)
            return
        remote_file_path = db(path_join(remote_folder_path, local_item))
        local_file_path = path_join(local_folder_path, local_item)

        if os.path.isdir(local_file_path):
            local_file_path = add_trailing_slash(local_file_path)

        if skip(local_file_path) or is_excluded_folder(local_file_path):
            continue
        if local_item_not_found_at_remote(remote_folder, remote_file_path):
            if (
                time_from_last_run > local_modified_time(local_file_path)
                and time_from_last_run > time.time() - 60 * 60 * 2
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

    for sub_folder in os.listdir(local_folder_path):
        if os.path.isdir(local_folder_path + sub_folder):
            if not skip(local_folder_path + sub_folder):
                action_folder(
                    db(path_join(remote_folder_path, sub_folder))
                )


print("Drupebox sync started at", readable_time(time.time()))
file_tree_from_last_run = load_tree()
cursor_from_last_run, time_from_last_run = load_cursor()

remotely_deleted_files = determine_remotely_deleted_files(cursor_from_last_run)
action_locally_deleted_files()

fyi("Syncing all other local and remote files changes")
action_folder("")

store_live_cursor()
store_tree(get_live_tree())
print("Drupebox sync complete at", readable_time(time.time()))
