import os
import re
from dotenv import load_dotenv

import yaml

from lib.utils import abs_path


def substitute_env_vars(data):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = substitute_env_vars(value)

    if isinstance(data, list):
        for i, value in enumerate(data):
            data[i] = substitute_env_vars(value)

    elif isinstance(data, str):
        # Find all occurrences of $ENV_VAR
        matches = re.findall(r'\$([A-Za-z_][A-Za-z0-9_]*)', data)

        # Replace each occurrence with the corresponding environment variable value
        for match in matches:
            env_var_value = os.environ.get(match, f"${match}")
            data = data.replace(f"${match}", env_var_value)

    return data


def load_config(filename):
    load_dotenv(
        dotenv_path=abs_path('.env'),
        verbose=True,
    )

    with open(abs_path(filename)) as f:
        config = yaml.safe_load(f)

    return substitute_env_vars(config)
