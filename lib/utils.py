import base64
import mimetypes
import os
import uuid
from io import BytesIO

import requests


def asset_filename(user_id, filename):
    return f"assets/{user_id}/{filename}"


def upload_asset(db, storage, chat_id, filepath):
    if filepath.startswith('http'):
        data = requests.get(filepath).content
    else:
        with open(filepath, 'rb') as f:
            data = f.read()

    origfilename = filepath.split('/')[-1]
    ext = origfilename.split('.')[-1]
    if '?' in ext:
        ext = ext.split('?')[0]

    filename = uuid.uuid4().hex + '.' + ext
    asset = db.save_asset(chat_id, filename)

    storage.save_data(
        data,
        asset_filename(chat_id, filename),
        mimetype=mimetypes.guess_type(origfilename)[0],
    )
    return asset


def abs_path(path):
    return os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", path))


def is_empty(txt):
    return txt is None or (isinstance(txt, str) and txt.strip() == '') or False


def locale(context):
    if context.get('language', 'en') == 'br':
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


def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    d = base64.b64encode(buffered.getvalue()).decode('utf-8')
    if not d.startswith('data:image/png;base64,'):
        d = 'data:image/png;base64,' + d
    return d
