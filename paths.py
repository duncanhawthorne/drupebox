#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

home = os.path.expanduser("~")


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


def get_containing_folder_path(file_path):
    # rstrip for safety
    return path_join(*tuple(file_path.rstrip("/").split("/")[0:-1]))


def get_file_name(local_file_path):
    return local_file_path.rstrip("/").split("/")[-1]  # rstrip for safety only


def path_exists(path):
    return os.path.exists(path)


if sys.platform != "win32":
    drupebox_cache_folder = "/dev/shm"
else:
    drupebox_cache_folder = path_join(home, ".config")
