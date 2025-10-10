#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
from datetime import datetime, timezone


def readable_time(unix_time):
    return (
        datetime.fromtimestamp(float(unix_time), tz=timezone.utc).strftime(
            "%a, %d %b %Y %H:%M:%S +0000"
        )
        + " UTC"
    )


def is_server_connection_stale(t):
    return time.time() > t + 60


def is_recent_last_run(t):
    # ensures have run drupebox recently
    # This test is used before delete local file
    # when find a local file and no file at remote and file is showing in dropbox remotely_deleted_files.
    # If ran drupebox recently then must have deleted on drupebox recently.
    # If haven't ran drupebox recently there is higher risk this is not an intentional remote deletion,
    # and therefore don't take the risk to delete local file
    return t > time.time() - 60 * 60 * 2


is_windows = os.path.sep == "\\" and sys.platform == "win32"
