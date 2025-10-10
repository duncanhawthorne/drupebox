#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

import config
import paths


def _get_live_local_tree():
    # get full list of local files in the Drupebox folder
    tree = []
    for root, dirs, files in os.walk(
        config.dropbox_local_path, topdown=True, followlinks=True
    ):
        root = paths.unix_slash(root)  # format with forward slashes on all platforms
        dirs[:] = [
            d
            for d in dirs
            if paths.add_trailing_slash(paths.join(root, d))
            not in config.excluded_folder_paths
        ]  # test with slash at end to match excluded_folder_paths and to ensure prefix-free matching
        for name in files:
            tree.append(paths.join(root, name))
        for name in dirs:
            tree.append(paths.join(root, name))
    # Sort longest to smallest so that files get processed before their parent folders.
    tree.sort(key=len, reverse=True)
    return tree


def _store_tree(tree):
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


def determine_locally_deleted_files():
    # need to maintain order of two lists
    tree_now = _get_live_local_tree()
    tree_last = _file_tree_from_last_run
    return [element for element in tree_last if element not in tree_now]


def store_current_tree():
    _store_tree(_get_live_local_tree())


_tree_cache_file = paths.join(paths.cache_folder, config.APP_NAME + "_last_seen_files")
_file_tree_from_last_run = _load_tree()
