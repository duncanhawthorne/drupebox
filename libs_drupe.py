#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import dropbox
from send2trash import send2trash
from datetime import datetime, timezone
from configobj import ConfigObj


"""
Variables in the following formats
remote_file_path -> dropbox format
remote_folder_path -> dropbox format (for the avoidance of doubt, no trailing slash)
local_file_path -> posix format, no trailing slash
local_folder_path -> posix format, no trailing slash
"""


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


def note(text):
    print(">>>", text)


def alert(text):
    print("!!!", text)


def fyi(text):
    print("   ", text)


def fyi_ignore(text):
    print("     -> ignore", text)


def path_join(*paths):
    paths_list = list(paths)
    # enable joining /X with /Y to form /X/Y, given that os.path.join would just produce /Y
    for i in range(len(paths_list)):
        if i > 0:
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
    return path1.rstrip("/")


def get_remote_file_path_of_local_file_path(local_file_path):
    return db(local_file_path[len(dropbox_local_path) :])


def get_containing_folder_path(file_path):
    # rstrip for safety
    return path_join(*tuple(file_path.rstrip("/").split("/")[0:-1]))


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
    for root, dirs, files in os.walk(
        dropbox_local_path, topdown=True, followlinks=True
    ):
        root = unix_slash(root)  # format with forward slashes on all platforms
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
    with open(drupebox_cache_file_list_path, "wb") as f:
        f.write(bytes(tree.encode()))


def load_tree():
    if os.path.exists(drupebox_cache_file_list_path):
        with open(drupebox_cache_file_list_path, "r") as f:
            last_tree = f.read().split("\n")
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
    except:
        note("Tried to delete file on dropbox, but it was not there")


def readable_time(unix_time):
    return (
        datetime.fromtimestamp(float(unix_time), tz=timezone.utc).strftime(
            "%a, %d %b %Y %H:%M:%S +0000"
        )
        + " UTC"
    )


def is_file(remote_item):
    return not isinstance(remote_item, dropbox.files.FolderMetadata)


def path_exists(path):
    return os.path.exists(path)


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
        if (
            local_folder_path_with_slash[0 : len(excluded_folder_path)]
            == excluded_folder_path
        ):
            print("exc", remote_file_path)
            return True
    return False


def local_item_not_found_at_remote(remote_folder, remote_file_path):
    unaccounted_local_file = True
    for remote_item in remote_folder:
        if remote_item.path_display == remote_file_path:
            unaccounted_local_file = False
    return unaccounted_local_file


def load_last_state():
    config_filename = drupebox_cache_last_state_path
    if not path_exists(config_filename):
        config_tmp = ConfigObj()
        config_tmp.filename = config_filename
        config_tmp["cursor_from_last_run"] = ""
        config_tmp["time_from_last_run"] = 0
        config_tmp["excluded_folder_paths_from_last_run"] = []
    else:
        config_tmp = ConfigObj(config_filename)
        config_tmp["time_from_last_run"] = float(config_tmp["time_from_last_run"])
    return config_tmp


def save_last_state():
    config_filename = drupebox_cache_last_state_path
    config_tmp = ConfigObj(config_filename)
    config_tmp["cursor_from_last_run"] = db_client.files_list_folder_get_latest_cursor(
        "", recursive=True
    ).cursor
    config_tmp["time_from_last_run"] = time.time()
    config_tmp["excluded_folder_paths_from_last_run"] = excluded_folder_paths
    config_tmp.write()


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


home = os.path.expanduser("~")

if sys.platform != "win32":
    drupebox_cache = "/dev/shm/"
else:
    drupebox_cache = add_trailing_slash(path_join(home, ".config"))

drupebox_cache_file_list_path = path_join(drupebox_cache, APP_NAME + "_last_seen_files")
drupebox_cache_last_state_path = path_join(drupebox_cache, APP_NAME + "_last_state")

config = get_config()

dropbox_local_path = config["dropbox_local_path"]
excluded_folder_paths = config["excluded_folder_paths"]

file_tree_from_last_run = load_tree()
last_state = load_last_state()
time_from_last_run = last_state["time_from_last_run"]

db_client = dropbox.Dropbox(
    app_key=config["app_key"], oauth2_refresh_token=config["refresh_token"]
)
