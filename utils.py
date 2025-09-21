#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime, timezone


def readable_time(unix_time):
    return (
        datetime.fromtimestamp(float(unix_time), tz=timezone.utc).strftime(
            "%a, %d %b %Y %H:%M:%S +0000"
        )
        + " UTC"
    )
