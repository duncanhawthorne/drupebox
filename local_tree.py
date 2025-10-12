#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from itertools import chain
from typing import List, Set

import config
import paths

_tree_cache_file = paths.join(paths.cache_folder, config.APP_NAME + "_last_seen_files")


def _get_live_local_tree() -> Set[str]:
    """Gets a list of all files and directories in the local Dropbox folder."""
    # get full list of local files in the Drupebox folder
    tree = set()
    excluded_paths_set = set(config.excluded_folder_paths)
    for root, dirs, files in os.walk(
        config.dropbox_local_path, topdown=True, followlinks=True
    ):
        root = paths.unix_slash(root)  # format with forward slashes on all platforms
        dirs[:] = (
            d
            for d in dirs
            if paths.add_trailing_slash(paths.join(root, d)) not in excluded_paths_set
        )  # test with slash at end to match excluded_folder_paths and to ensure prefix-free matching
        tree.update(paths.join(root, name) for name in chain(files, dirs))
    return tree


def _load_tree() -> Set[str]:
    """Loads the local file tree from the cache file."""
    if not paths.exists(_tree_cache_file):
        return set()
    with open(_tree_cache_file, "r", encoding="utf-8") as f:
        return set(f.read().splitlines())


def _store_tree(tree: Set[str]):
    """Stores the local file tree to a cache file."""
    with open(_tree_cache_file, "w", encoding="utf-8") as f:
        f.write("\n".join(tree))


def determine_locally_deleted_files() -> List[str]:
    """Determines which files have been deleted locally since the last run."""
    tree_now = _get_live_local_tree()
    tree_last = _load_tree()
    deleted_files = tree_last - tree_now
    deleted_files_list = list(deleted_files)
    # Sort longest to smallest so that files get processed before their parent folders.
    deleted_files_list.sort(key=len, reverse=True)
    return deleted_files_list


def store_current_tree():
    """Stores the current local file tree to the cache file."""
    _store_tree(_get_live_local_tree())
