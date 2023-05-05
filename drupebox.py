#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from libs_drupe import *

config = get_config()

max_file_size = int(config["max_file_size"])
dropbox_local_path = config["dropbox_local_path"]

db_client = dropbox.Dropbox(
    app_key=app_key, oauth2_refresh_token=config["refresh_token"]
)


def action_locally_deleted_files():
    fyi("Actioning locally deleted files")
    file_tree_from_last_run = load_tree()
    file_tree_now = get_live_tree()
    locally_deleted_files = determine_locally_deleted_files(
        file_tree_now, file_tree_from_last_run
    )
    for locally_deleted_file in locally_deleted_files:
        note("Found local file deleted, so delete on dropbox " + locally_deleted_file)
        try:
            db_client.files_delete(
                "/" + locally_deleted_file[len(dropbox_local_path) :]
            )
        except:
            note(
                "Tried to delete a file on dropbox, but it was not there "
                + locally_deleted_file
            )
    store_tree(file_tree_now)


def action_folder(remote_folder_path):
    fyi(remote_folder_path)
    for excluded_path in config["excluded_paths"]:
        if remote_folder_path[0 : len(excluded_path)] == excluded_path:
            note("Path excluded")
            return
    local_folder_path = dropbox_local_path + remote_folder_path

    remote_folder = db_client.files_list_folder(fp(remote_folder_path)).entries
    remote_folder_checked_time = time.time()
    for remote_item in remote_folder:
        if time.time() > remote_folder_checked_time + 60:
            note("last checked in with server over 60 seconds ago, refreshing")
            action_folder(remote_folder_path)
            return
        remote_file_path = remote_item.path_display
        local_file_path = dropbox_local_path + remote_file_path[1:]
        if (
            not path_exists(local_file_path)
            or not isinstance(remote_item, dropbox.files.FolderMetadata)
            and unix_time(remote_item.client_modified)
            > local_item_modified_time(local_file_path)
        ):  # unix_time(remote_item['modified']) > local_item_modified_time(local_file_path):
            note(
                "Found new file on remote, or remote file has been updated - downloading "
                + remote_file_path
            )
            if isinstance(remote_item, dropbox.files.FolderMetadata):
                if not path_exists(local_file_path):
                    os.makedirs(local_file_path)
                else:
                    "Modification time on a folder does not matter - no action"

            else:
                download(db_client, remote_file_path, local_file_path)
                fix_local_time(db_client, remote_file_path)

        elif not isinstance(
            remote_item, dropbox.files.FolderMetadata
        ) and local_item_modified_time(local_file_path) > unix_time(
            remote_item.client_modified
        ):

            if not isinstance(remote_item, dropbox.files.FolderMetadata):
                note("Local file has been updated - uploading " + remote_file_path)
                if os.path.getsize(local_file_path) < max_file_size:
                    upload(db_client, local_file_path, remote_file_path)
                    fix_local_time(db_client, remote_file_path)
                else:
                    note("File above max size, ignoring: " + remote_file_path)
            else:
                "Modification time on a folder does not matter - no action"

    for local_item in os.listdir(local_folder_path):
        if time.time() > remote_folder_checked_time + 60:
            note("last checked in with server over 60 seconds ago, refreshing")
            action_folder(remote_folder_path)
            return
        remote_file_path = "/" + remote_folder_path + local_item
        local_file_path = local_folder_path + local_item
        if skip(local_file_path):
            continue
        if local_item_not_found_at_remote(remote_folder, remote_file_path):
            local_time = local_item_modified_time(local_file_path)
            remote_time_of_deleted_file = False  # remote_item_modified_with_deleted(db_client, remote_file_path) #Can't do this test currently, so blanking, and never do local delete following delete on server
            if (
                False and remote_time_of_deleted_file > local_time
            ):  # Can't do this test currently, so blanking, and never do local delete following delete on server
                note(
                    "Unnaccounted file - Modified time for deleted remote file is latest - delete "
                    + remote_file_path
                )
                if os.path.isdir(local_file_path):
                    os.rmdir(local_file_path)
                else:
                    os.remove(local_file_path)
            else:
                note(
                    "Unnaccounted file - Local is latest to modified - upload "
                    + remote_file_path
                )
                if os.path.isdir(local_file_path):
                    note(
                        "New file is a folder, dont upload it but just create a folder directly on dropbox - subfiles will get picked up later "
                        + remote_file_path
                    )
                    db_client.files_create_folder(remote_file_path)
                else:
                    if os.path.getsize(local_file_path) < max_file_size:
                        upload(db_client, local_file_path, remote_file_path)
                        fix_local_time(db_client, remote_file_path)
                    else:
                        note("File above max size, ignoring: " + remote_file_path)

    for sub_folder in os.listdir(local_folder_path):
        if os.path.isdir(local_folder_path + sub_folder):
            if not skip(local_folder_path + sub_folder):
                action_folder(remote_folder_path + sub_folder + "/")


action_locally_deleted_files()
fyi("Actioning all other local and remote files changes")
action_folder("")
print("Sync complete at ", readable_time(time.time()))
