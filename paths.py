#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

import utils

home = os.path.expanduser("~")


def exists(path):
    return os.path.exists(path)


def join(first_path, *other_paths):
    assert len(other_paths) >= 1
    # enable joining /X with /Y to form /X/Y, given that os.path.join would just produce /Y
    other_paths_list = [item.lstrip("/") for item in other_paths]
    return unix_slash(os.path.join(first_path, *other_paths_list))


def unix_slash(path):
    if utils.is_windows:
        return path.replace("\\", "/")
    else:  # safer to not make any edit if possible as linux files can contain backslashes
        return path


def system_slash(path):
    if utils.is_windows:
        return path.replace("/", os.path.sep)
    else:  # safer to not make any edit if possible as linux files can contain backslashes
        return path


def add_trailing_slash(path):
    # folder in format with trailing forward slash
    path = unix_slash(path)
    if not path.endswith("/"):
        path = path + "/"
    return path


def dbfmt(path):
    # Fix path for use in dropbox, i.e. to have leading slash, except dropbox root folder is "" not "/"
    if path == "":
        return path
    if path == "/":
        return ""
    if not path.startswith("/"):
        path = "/" + path
    return path.rstrip("/")


def get_containing_db_folder_path(remote_file_path):
    # rstrip for safety
    return remote_file_path.rstrip("/").rsplit("/", 1)[0]


def get_file_name(local_file_path):
    # rstrip for safety
    return local_file_path.rstrip("/").rsplit("/", 1)[1]


if not utils.is_windows:
    if os.path.exists("/dev/shm"):
        cache_folder = "/dev/shm"
    else:
        cache_folder = "/tmp"
else:
    cache_folder = join(home, ".config")
