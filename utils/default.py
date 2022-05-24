import time
import json
from collections import namedtuple


def get(file):
    try:
        with open(file, encoding="utf8") as data:
            return json.load(
                data, object_hook=lambda d: namedtuple("X", d.keys())(*d.values())
            )
    except AttributeError:
        raise AttributeError("Unknown argument")
    except FileNotFoundError:
        raise FileNotFoundError("JSON file wasn't found")


def timetext(name):
    return f"{name}_{int(time.time())}.txt"


def date(target):
    return target.strftime("%d %B %Y, %H:%M")
