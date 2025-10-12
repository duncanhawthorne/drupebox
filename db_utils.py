import os
import time
from datetime import timezone
from functools import cache

import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import FileMetadata
from send2trash import send2trash

import config
import log
import paths
import state_cache
import utils
from config import get_remote_file_path, get_local_file_path

"""
Variables in the following formats
remote_file_path -> dropbox format
remote_folder_path -> dropbox format (for the avoidance of doubt, no trailing slash)
local_file_path -> posix format, no trailing slash
local_folder_path -> posix format, no trailing slash
"""

_db_client = dropbox.Dropbox(
    app_key=config.app_key, oauth2_refresh_token=config.refresh_token
)


def upload(local_file_path, remote_file_path):
    """Uploads a local file to Dropbox."""
    if not config.file_size_ok(local_file_path):
        log.note("File above max size, ignoring: " + remote_file_path)
        return
    print("upload", remote_file_path)
    with open(local_file_path, "rb") as f:
        remote_file = _db_client.files_upload(
            f.read(),
            remote_file_path,
            mute=True,
            mode=dropbox.files.WriteMode("overwrite", None),
        )
    _fix_local_time(remote_file, remote_file_path)


def create_remote_folder(remote_file_path):
    """Creates a folder on Dropbox."""
    print("create", remote_file_path)
    _db_client.files_create_folder_v2(remote_file_path)


def create_local_folder(remote_file_path, local_file_path):
    """Creates a local folder."""
    print("create", remote_file_path)
    os.makedirs(local_file_path, exist_ok=True)


def download_file(remote_file_path, local_file_path):
    """Downloads a file from Dropbox to the local filesystem."""
    print("downld", remote_file_path)
    if paths.exists(local_file_path):
        _delete_real(local_file_path)
    remote_file = _db_client.files_download_to_file(local_file_path, remote_file_path)
    _fix_local_time(remote_file, remote_file_path)


def local_delete(local_file_path):
    """Deletes a local file by sending it to the trash."""
    remote_file_path = get_remote_file_path(local_file_path)
    assert (
        config.ok_to_delete_files()
    )  # as already checked this before calling local_delete
    log.alert(remote_file_path)
    _delete_real(local_file_path)


def _delete_real(local_file_path):
    """Sends a file to the system's trash."""
    # deleting local files uses send2trash so no files are permanently deleted locally
    send2trash(paths.system_slash(local_file_path))


def remote_delete(local_file_path):
    """Deletes a file from Dropbox."""
    remote_file_path = get_remote_file_path(local_file_path)
    log.alert(remote_file_path)
    try:
        _db_client.files_delete_v2(remote_file_path)
    except ApiError as err:
        if (
            hasattr(err.error, "is_path_lookup")
            and err.error.is_path_lookup()
            and hasattr(err.error.get_path_lookup(), "is_not_found")
            and err.error.get_path_lookup().is_not_found()
        ):
            log.note("Tried to delete file on dropbox, but it was not there")
        else:
            log.note("Unexpected Dropbox API error on delete: " + str(err))


def is_file(remote_item):
    """Checks if a Dropbox item is a file."""
    return not isinstance(remote_item, dropbox.files.FolderMetadata)


def local_modified_time(local_file_path):
    """Gets the modification time of a local file."""
    return os.path.getmtime(local_file_path)


def remote_modified_time(remote_item):
    """Gets the modification time of a remote Dropbox item."""
    db_naive_time = remote_item.client_modified
    db_utc_time = db_naive_time.replace(tzinfo=timezone.utc)
    return db_utc_time.timestamp()


def _fix_local_time(remote_file, remote_file_path):
    """Sets the local file's modification time to match the remote file."""
    log.note("Fix local time for file")
    file_modified_time = remote_modified_time(remote_file)
    local_file_path = get_local_file_path(remote_file_path)
    os.utime(
        local_file_path,
        (
            int(file_modified_time),
            int(file_modified_time),
        ),
    )


def get_remote_folder(remote_folder_path):
    """Gets the contents of a remote folder."""
    return [
        element
        for element in _get_all_remote_files()
        if paths.get_containing_db_folder_path(element.path_display)
        == remote_folder_path
    ]


def _get_all_remote_files_real():
    """Fetches the list of all remote files from Dropbox."""
    return _db_client.files_list_folder("", recursive=True).entries


_CACHE_TIME_KEY = "checked_time"
_CACHE_DATA_KEY = "data"


_all_remote_files_cache = {_CACHE_TIME_KEY: 0.0, _CACHE_DATA_KEY: []}


def _get_all_remote_files():
    """Gets a cached list of all remote files."""
    if utils.is_server_connection_stale(_all_remote_files_cache[_CACHE_TIME_KEY]):
        if _all_remote_files_cache[_CACHE_TIME_KEY] != 0:
            log.note("Last checked in with server over 60 seconds ago, refreshing")
        else:
            log.fyi("Scanning for files on Dropbox")
        _all_remote_files_cache[_CACHE_DATA_KEY] = _get_all_remote_files_real()
        _all_remote_files_cache[_CACHE_TIME_KEY] = time.time()
    return _all_remote_files_cache[_CACHE_DATA_KEY]


def item_not_found_at_remote(remote_folder, remote_file_path):
    """Checks if an item is not found in the remote folder."""
    return not any(
        remote_item.path_display == remote_file_path for remote_item in remote_folder
    )


def _determine_remotely_deleted_files():
    """Determines which files have been deleted on Dropbox since the last run."""
    cursor_last_run = state_cache.cursor_from_last_run
    log.fyi("Scanning for any remotely deleted files since last Drupebox run")
    if cursor_last_run == "":
        return []
    deleted_files = [
        delta.path_display
        for delta in _db_client.files_list_folder_continue(cursor_last_run).entries
        if isinstance(delta, dropbox.files.DeletedMetadata)
    ]
    if deleted_files:  # test not empty
        log.note("The following files were deleted on Dropbox since last run")
        for deleted_file in deleted_files:
            log.note(deleted_file)
    return deleted_files


@cache
def remotely_deleted_files():
    """Gets a cached list of remotely deleted files."""
    # uses cache decorator, so after first call, just returns cache of last call
    return _determine_remotely_deleted_files()


def get_latest_state():
    """Gets the latest cursor from Dropbox."""
    return _db_client.files_list_folder_get_latest_cursor("", recursive=True).cursor
