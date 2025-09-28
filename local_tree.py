#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from config import excluded_folder_paths, dropbox_local_path, APP_NAME
from paths import unix_slash, add_trailing_slash, path_join, cache_folder


def get_live_local_tree():
    # get full list of local files in the Drupebox folder
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
    # Sort longest to smallest so that files get processed before their parent folders.
    tree.sort(key=len, reverse=True)
    return tree


def store_tree(tree):
    with open(_tree_cache_file, "w", encoding="utf-8") as f:
        f.write("\n".join(tree))


def _load_tree():
    if not os.path.exists(_tree_cache_file):
        return []
    with open(_tree_cache_file, "r", encoding="utf-8") as f:
        content = f.read()
        if not content:
            return []
        return content.split("\n")


def determine_locally_deleted_files(tree_now, tree_last):
    deleted = []
    if not tree_last:  # i.e. tree_last == []
        return []
    for element in tree_last:
        if not element in tree_now:
            deleted.append(element)
    return deleted


_tree_cache_file = path_join(cache_folder, APP_NAME + "_last_seen_files")

file_tree_from_last_run = _load_tree()
