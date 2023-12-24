import os


def abs_path(path):
    return os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", path))


def is_empty(txt):
    return txt is None or (isinstance(txt, str) and txt.strip() == '') or False


def is_blank(hash, key):
    if key not in hash or is_empty(hash[key]):
        return True
    return False


def get_or_default(hash, key, default):  # ignore nones
    if hash:
        if key not in hash or hash[key] is None:
            return default
        return hash[key]
    return None


def is_set(hash, key):
    return not is_blank(hash, key)


