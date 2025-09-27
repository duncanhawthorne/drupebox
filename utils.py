#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
    # safety to ensure can trust last cache
    return t > time.time() - 60 * 60 * 2
