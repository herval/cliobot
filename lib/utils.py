import base64
import os
import shlex
from io import BytesIO


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

def parse_command_line(command_line, pydantic_type):
    tokens = shlex.split(command_line)
    args = {}

    # Using a variable to remember the last parameter name
    last_param = None
    for token in tokens:
        if token.startswith('-'):
            # Normalize the parameter name (remove leading dashes)
            normalized_param = token.lstrip('-')
            last_param = normalized_param
        else:
            if last_param:
                args[last_param] = token
                last_param = None

    return pydantic_type(**args)