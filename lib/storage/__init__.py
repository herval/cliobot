import os


class LocalStorage:
    '''save image to local storage'''

    def __init__(self, folder="./"):
        self.folder = folder
        os.makedirs(folder, exist_ok=True)

    def save_data(self, data, path, mimetype):
        if path.startswith('/'):
            path = path[1:]

        os.makedirs(os.path.join(self.folder, os.path.dirname(path)), exist_ok=True)
        with open(os.path.join(self.folder, path), 'wb') as f:
            f.write(data)

    def full_path(self, path):
        return os.path.join(self.base_path(), path)

    def base_path(self):
        return self.folder

    def exists(self, path):
        return os.path.exists(os.path.join(self.folder, path))

    def get_data(self, path):
        with open(os.path.join(self.folder, path), 'rb') as f:
            return f.read()

    def stream_data(self, path, localpath):
        remote = os.path.join(self.folder, path)
        if not os.path.exists(remote):
            raise FileNotFoundError(remote)

        with open(remote, 'rb') as f:
            with open(localpath, 'wb') as f2:
                f2.write(f.read())