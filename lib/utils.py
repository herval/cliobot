import base64
import hashlib
import io
import os
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image


def md5_hash(txt):
    md5 = hashlib.md5()
    md5.update(txt.encode())
    return md5.hexdigest()


def abs_path(path):
    return os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", path))


def is_empty(txt):
    return txt is None or (isinstance(txt, str) and txt.strip() == '') or False


def locale(session):
    if session.get('language', 'en') == 'br':
        return 'br'
    else:
        return 'en'


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


def flatten(lst):
    flat_list = []
    for item in lst:
        if isinstance(item, list):
            flat_list.extend(flatten(item))
        else:
            flat_list.append(item)
    return flat_list


def download_string(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r.text

def decode_image(file_or_url) -> str:
    """
    convert a file to base64 if it's local or use the url if remote

    :param file_or_url:
    :return:
    """
    if isinstance(file_or_url, Path):
        return image_to_base64(Image.open(file_or_url))
    elif file_or_url.startswith('data:image/png;base64,'):
        return file_or_url
    elif file_or_url.startswith('/'):
        with open(file_or_url, "rb") as f:
            binary_data = f.read()
        return image_to_base64(Image.open(io.BytesIO(binary_data)))
    else:
        return file_or_url  # full url


def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    d = base64.b64encode(buffered.getvalue()).decode('utf-8')
    if not d.startswith('data:image/png;base64,'):
        d = 'data:image/png;base64,' + d
    return d


def open_image(r):
    if r.startswith('http'):
        return Image.open(BytesIO(download(r)))
    return Image.open(r)


def download(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r.content
    else:
        raise Exception(f"Failed to download {url} {r.status_code}")
