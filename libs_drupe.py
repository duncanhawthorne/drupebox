#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import dropbox
from send2trash import send2trash
from datetime import datetime


"""
Variables in the following fomrats
remote_file_path -> dropbox format
remote_folder_path -> dropbox format (for the avoidance of doubt, no trailing slash)
local_file_path -> posix format, no trailing slash
local_folder_path -> posix format, with trailing slash
"""


def note(text):
    print(">>> " + text)


def fyi(text):
    print("    " + text)


def fyi_ignore(text):
    print("     -> ignore " + text)


def path_join(*paths):
    paths_list = list(paths)
    # enable joining /X with /Y to form /X/Y, given that os.path.join would just produce /Y
    for i in range(len(paths_list)):
        if i > 0 and len(paths_list[i]) > 0 and paths_list[i][0] == "/":
            paths_list[i] = paths_list[i].lstrip("/")
    return unix_slash(os.path.join(*tuple(paths_list)))


def unix_slash(path):
    if os.path.sep == "\\" and sys.platform == "win32":
        return path.replace("\\", "/")
    else:  # safer to not make any edit if possible as linux files can contain backslashes
        return path


def system_slash(path):
    if os.path.sep == "\\" and sys.platform == "win32":
        return path.replace("/", os.path.sep)
    else:  # safer to not make any edit if possible as linux files can contain backslashes
        return path


def add_trailing_slash(path):
    # folder in format with trailing forward slash
    path = unix_slash(path)
    if path[-1] != "/":
        path = path + "/"
    return path


def strip_trailing_slash(path):
    if path[-1] == "/":
        path = path[:-1]
    return path


def db(path):
    # Fix path for use in dropbox, i.e. to have leading slash, except dropbox root folder is "" not "/"
    if path == "":
        return path
    if path == "/":
        return ""
    else:
        if path[0] != "/":
            path1 = "/" + path
        else:
            path1 = path
    return strip_trailing_slash(path1)


def get_remote_file_path_of_local_file_path(local_file_path):
    return db(local_file_path[len(dropbox_local_path) :])


def get_config_real():
    from configobj import ConfigObj

    if not path_exists(path_join(home, ".config")):
        os.makedirs(path_join(home, ".config"))
    config_filename = path_join(home, ".config", "drupebox")
    if not path_exists(config_filename):
        # First time only
        config = ConfigObj()
        config.filename = config_filename

        # To customise this code, change the app key below
        # Get your app key from the Dropbox developer website for your app
        config["app_key"] = "1skff241na3x0at"

        flow = dropbox.DropboxOAuth2FlowNoRedirect(
            config["app_key"], use_pkce=True, token_access_type="offline"
        )
        authorize_url = flow.start()
        print(("1. Go to: " + authorize_url))
        print('2. Click "Allow" (you might have to log in first)')
        print("3. Copy the authorization code.")
        code = input("Enter the authorization code here: ").strip()
        result = flow.finish(code)

        config["refresh_token"] = result.refresh_token
        config["dropbox_local_path"] = unix_slash(
            input(
                "Enter dropbox local path (or press enter for "
                + path_join(home, "Dropbox")
                + "/) "
            ).strip()
        )
        if config["dropbox_local_path"] == "":
            config["dropbox_local_path"] = path_join(home, "Dropbox")
        config["dropbox_local_path"] = add_trailing_slash(config["dropbox_local_path"])
        if not path_exists(config["dropbox_local_path"]):
            os.makedirs(config["dropbox_local_path"])
        config["max_file_size"] = 10000000
        config["excluded_folder_paths"] = [
            "/home/pi/SUPER_SECRET_LOCATION_1/",
            "/home/pi/SUPER SECRET LOCATION 2/",
        ]
        config["really_delete_local_files"] = False
        config.write()

    config = ConfigObj(config_filename)

    # Sanitize config

    # format dropbox local path with forward slashes on all platforms and end with forward slash to ensure prefix-free
    if config["dropbox_local_path"] != add_trailing_slash(config["dropbox_local_path"]):
        config["dropbox_local_path"] = add_trailing_slash(config["dropbox_local_path"])
        config.write()

    # format excluded paths with forward slashes on all platforms and end with forward slash to ensure prefix-free
    excluded_folder_paths_sanitize = False
    for excluded_folder_path in config["excluded_folder_paths"]:
        if add_trailing_slash(excluded_folder_path) != excluded_folder_path:
            excluded_folder_paths_sanitize = True
            break

    if excluded_folder_paths_sanitize:
        excluded_folder_paths = []
        excluded_folder_paths[:] = [
            add_trailing_slash(excluded_folder_path)
            for excluded_folder_path in config["excluded_folder_paths"]
        ]
        config["excluded_folder_paths"] = excluded_folder_paths
        config.write()

    return config


def get_config():
    if get_config.cache == "":  # First run
        get_config.cache = get_config_real()
    return get_config.cache


get_config.cache = ""


def config_ok_to_delete():
    if get_config()["really_delete_local_files"] != "True":
        note("Drupebox not set to delete local files, so force reupload local file")
        return False
    else:
        return True


def get_live_tree():
    # get full list of files in the Drupebox folder
    tree = []
    for (root, dirs, files) in os.walk(
        dropbox_local_path, topdown=True, followlinks=True
    ):
        root = unix_slash(root)  # format with forward slashes on all plaforms
        dirs[:] = [
            d
            for d in dirs
            if add_trailing_slash(path_join(root, d)) not in excluded_folder_paths
        ]  # test with slash at end to match excluded_folder_paths and to ensure prefix-free matching
        for name in files:
            tree.append(path_join(root, name))
        for name in dirs:
            tree.append(path_join(root, name))
    tree.sort(
        key=lambda s: -len(s)
    )  # sort longest to smallest so that later files get deleted before the folders that they are in
    return tree


def store_tree(tree):
    tree = "\n".join(tree)
    with open(drupebox_cache_store_path, "wb") as f:
        f.write(bytes(tree.encode()))


def load_tree():
    if os.path.exists(drupebox_cache_store_path):
        last_tree = open(drupebox_cache_store_path, "r").read().split("\n")
    else:
        last_tree = [""]
    return last_tree


def determine_locally_deleted_files(tree_now, tree_last):
    deleted = []
    if tree_last == [""]:
        return []
    for element in tree_last:
        if not element in tree_now:
            deleted.append(element)
    return deleted


def upload(local_file_path, remote_file_path):
    if os.path.getsize(local_file_path) < int(config["max_file_size"]):
        print("uuu", remote_file_path)
        f = open(local_file_path, "rb")
        db_client.files_upload(
            f.read(),
            remote_file_path,
            mute=True,
            mode=dropbox.files.WriteMode("overwrite", None),
        )
        fix_local_time(remote_file_path)
    else:
        note("File above max size, ignoring: " + remote_file_path)


def create_remote_folder(remote_file_path):
    print("ccc", remote_file_path)
    db_client.files_create_folder(remote_file_path)


def create_local_folder(remote_file_path, local_file_path):
    print("ccc", remote_file_path)
    if not path_exists(local_file_path):
        os.makedirs(local_file_path)
    else:
        "Modification time on a folder does not matter - no action"


def download_file(remote_file_path, local_file_path):
    print("ddd", remote_file_path)
    if os.path.exists(local_file_path):
        send2trash(
            system_slash(local_file_path)
        )  # so no files permanently deleted locally
    db_client.files_download_to_file(local_file_path, remote_file_path)
    fix_local_time(remote_file_path)


def local_delete(local_file_path):
    remote_file_path = get_remote_file_path_of_local_file_path(local_file_path)
    if config_ok_to_delete():  # safety check that should be impossible to get to
        print("!!!", remote_file_path)
        send2trash(system_slash(local_file_path))


def remote_delete(local_file_path):
    remote_file_path = get_remote_file_path_of_local_file_path(local_file_path)
    print("!!!", remote_file_path)
    try:
        db_client.files_delete(remote_file_path)
    except:
        note("Tried to delete file on dropbox, but it was not there")


def unix_time(readable_time):
    return time.mktime(readable_time.timetuple())


def readable_time(unix_time):
    return datetime.fromtimestamp(float(unix_time)).strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )


def is_file(remote_item):
    return not isinstance(remote_item, dropbox.files.FolderMetadata)


def path_exists(path):
    return os.path.exists(path)


def local_modified_time(local_file_path):
    return os.path.getmtime(local_file_path)


def remote_modified_time(remote_item):
    return unix_time(remote_item.client_modified)


def fix_local_time(remote_file_path):
    remote_folder_path = db(
        path_join(*tuple(remote_file_path.split("/")[0:-1]))
    )  # path excluding file, i.e. just to the folder
    note("Fix local time for file")
    remote_folder = db_client.files_list_folder(remote_folder_path).entries
    for remote_file in remote_folder:
        if remote_file.path_display == remote_file_path:
            # matched the file we are looking for
            file_modified_time = remote_file.client_modified
            local_file_path = path_join(dropbox_local_path, remote_file_path[1:])
            os.utime(
                local_file_path,
                (
                    int(unix_time(file_modified_time)),
                    int(unix_time(file_modified_time)),
                ),
            )
            return  # found file so no further looping required


def skip(local_file_path):
    local_item = strip_trailing_slash(local_file_path).split("/")[-1]
    if local_item[0 : len(".fuse_hidden")] == ".fuse_hidden":
        fyi_ignore("fuse hidden files")
        return True
    if local_item[-len(".pyc") :] == ".pyc":
        fyi_ignore(".pyc files")
        return True
    if local_item[-len("__pycache__") :] == "__pycache__":
        fyi_ignore("__pycache__")
        return True
    if local_item[-len(".git") :] == ".git":
        fyi_ignore(".git")
        return True
    if local_item in [".DS_Store", "._.DS_Store", "DG1__DS_DIR_HDR", "DG1__DS_VOL_HDR"]:
        fyi_ignore(local_item)
        return True

    return False


def is_excluded_folder(local_folder_path):
    # forwad slash at end of path ensures prefix-free
    local_folder_path = add_trailing_slash(local_folder_path)
    remote_file_path = get_remote_file_path_of_local_file_path(local_folder_path)
    for excluded_folder_path in excluded_folder_paths:
        if local_folder_path[0 : len(excluded_folder_path)] == excluded_folder_path:
            print("exc", remote_file_path)
            return True
    return False


def local_item_not_found_at_remote(remote_folder, remote_file_path):
    unnaccounted_local_file = True
    for remote_item in remote_folder:
        if remote_item.path_display == remote_file_path:
            unnaccounted_local_file = False
    return unnaccounted_local_file


def store_live_cursor():
    cursor = db_client.files_list_folder_get_latest_cursor("", recursive=True).cursor
    result = cursor + "\n" + str(time.time())
    with open(drupebox_cache_cursor_path, "wb") as f:
        f.write(bytes(result.encode()))


def load_cursor():
    if os.path.exists(drupebox_cache_cursor_path):
        cursor = open(drupebox_cache_cursor_path, "r").read().split("\n")
    else:
        cursor = ["", "0"]
    cursor = [cursor[0], float(cursor[1])]
    return cursor


def determine_remotely_deleted_files(cursor):
    fyi("Scanning for any remotely deleted files since last Drupebox run")
    deleted_files = []
    if cursor != "":
        deltas = db_client.files_list_folder_continue(cursor).entries
        for delta in deltas:
            if isinstance(delta, dropbox.files.DeletedMetadata):
                deleted_files.append(delta.path_display)
    if deleted_files != []:
        note("The following files were deleted on Dropbox since last run")
        for deleted_file in deleted_files:
            note(deleted_file)
    return deleted_files


home = os.path.expanduser("~")

if sys.platform != "win32":
    drupebox_cache = "/dev/shm/"
else:
    drupebox_cache = add_trailing_slash(path_join(home, ".config"))

drupebox_cache_store_path = path_join(drupebox_cache, "drupebox_last_seen_files")
drupebox_cache_cursor_path = path_join(drupebox_cache, "drupebox_cursor")

config = get_config()

dropbox_local_path = config["dropbox_local_path"]
excluded_folder_paths = config["excluded_folder_paths"]

db_client = dropbox.Dropbox(
    app_key=config["app_key"], oauth2_refresh_token=config["refresh_token"]
)
