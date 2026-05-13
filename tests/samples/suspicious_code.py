"""Suspicious Python — should trigger detectors."""

import utils
import helpers
from misc import magic

import os
import sys
import json


def process_data(items: list) -> dict:
    result = {}
    for item in items:
        result[item] = item.upper()
    unused_var = 42

    if False:
        never_run()

    return result
    dead_code = "this never executes"


def never_run() -> None:
    print("dead function")


data = os.path.join("path", "to", "file")
text = open("test.txt").read()