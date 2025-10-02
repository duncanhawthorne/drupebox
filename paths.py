#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

home = os.path.expanduser("~")


def exists(path):
    return os.path.exists(path)


def join(first_path, *other_paths):
    other_paths_list = list(other_paths)
    assert len(other_paths_list) >= 1
    # enable joining /X with /Y to form /X/Y, given that os.path.join would just produce /Y
    for i in range(len(other_paths_list)):
        other_paths_list[i] = other_paths_list[i].lstrip("/")
    return unix_slash(os.path.join(first_path, *other_paths_list))


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
    if not path.endswith("/"):
        path = path + "/"
    return path


def db(path):
    # Fix path for use in dropbox, i.e. to have leading slash, except dropbox root folder is "" not "/"
    if path == "":
        return path
    if path == "/":
        return ""
    else:
        if not path.startswith("/"):
            path1 = "/" + path
        else:
            path1 = path
    return path1.rstrip("/")


def get_containing_db_folder_path(remote_file_path):
    # rstrip for safety
    path_list = remote_file_path.rstrip("/").split("/")[1:-1]
    if len(path_list) == 0:
        out = "/"
    elif len(path_list) == 1:
        out = path_list[0]
    else:
        out = join(*path_list)
    return db(out)


def get_file_name(local_file_path):
    return local_file_path.rstrip("/").split("/")[-1]  # rstrip for safety only


if sys.platform != "win32":
    cache_folder = "/dev/shm"
else:
    cache_folder = join(home, ".config")
