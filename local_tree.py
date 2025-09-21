#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from cache import drupebox_cache_file_list_path, load_last_state
from config import excluded_folder_paths, dropbox_local_path
from paths import unix_slash, add_trailing_slash, path_join


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
    if not os.path.exists(drupebox_cache_file_list_path):
        return []
    with open(drupebox_cache_file_list_path, "r") as f:
        content = f.read()
        if not content:
            return []
        return content.split("\n")


def determine_locally_deleted_files(tree_now, tree_last):
    deleted = []
    if tree_last == []:
        return []
    for element in tree_last:
        if not element in tree_now:
            deleted.append(element)
    return deleted


file_tree_from_last_run = load_tree()
