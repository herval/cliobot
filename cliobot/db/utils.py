import mimetypes
import os
from pathlib import Path

import requests

from cliobot.utils import md5_hash, abs_path, base64_to_bytes


def asset_filename(folder, user_id, filename):
    return f"{folder}/{user_id}/{filename}"


async def cached_get_file(file_id, bot, session) -> Path:
    """
    get a file_id and return the local path to the file
    if the file is already cached, return the cached file
    if the file_id is a url or a local path, download it to the cache folder and return the local path

    :param file_id:
    :param bot:
    :param session:
    :return:
    """
    info = await bot.messaging_service.get_file_info(file_id)
    filepath = info['file_path']

    af = abs_path(asset_filename('cache', session.user_id, hashed_filename(filepath)))
    if os.path.exists(af):
        return Path(af)

    os.makedirs(os.path.dirname(af), exist_ok=True)
    try:
        data = get_data(file_id)
    except FileNotFoundError as e:
        _, data = await bot.messaging_service.get_file(file_id)

    with open(af, 'wb') as f:
        f.write(data)

    return Path(af)


def get_data(filepath):
    if filepath.startswith('data:'):
        return base64_to_bytes(filepath)
    elif os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            data = f.read()
            return data
    elif filepath.startswith('http'):
        return requests.get(filepath).content
    else:
        with open(filepath, 'rb') as f:
            return f.read()


def hashed_filename(local_path):
    if local_path.startswith('data:'):
        ext = local_path.split(';')[0].split('/')[-1]
        return md5_hash(local_path) + '.' + ext

    ext = local_path.split('.')[-1]
    if '?' in ext:
        ext = ext.split('?')[0]
    return md5_hash(local_path) + '.' + ext


def upload_asset(
        session,
        local_path,
        db,
        storage,
        folder,
        file_id=None):
    data = get_data(local_path)

    storage_path = storage.save_data(
        data,
        asset_filename(folder, session.user_id, hashed_filename(local_path)),
        mimetype=mimetypes.guess_type(local_path)[0],
    )
    return db.save_asset(
        external_id=file_id or md5_hash(local_path),
        user_id=session.user_id,
        chat_id=session.chat_id,
        storage_path=storage_path,
    )
