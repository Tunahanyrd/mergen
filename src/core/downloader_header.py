#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Downloader with Python 3.14t free-threading support.

Optimized for GIL-free execution with 64 truly parallel threads.
"""

from concurrent.futures import ThreadPoolExecutor

# Python 3.14t free-threading: Shared executor for all downloads
# No GIL = 64 truly parallel threads!
_global_executor = None


def get_executor() -> ThreadPoolExecutor:
    """Get or create global thread pool executor for downloads."""
    global _global_executor
    if _global_executor is None:
        _global_executor = ThreadPoolExecutor(max_workers=64, thread_name_prefix="mergen-dl")
    return _global_executor
