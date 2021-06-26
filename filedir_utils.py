import os


def upload_blob(text, blob_name):
    with open(blob_name, 'w') as f:
        f.write(text)


def create_folder(folder_name):
    os.mkdir(folder_name)


def read_blob(blob_name):
    with open(blob_name, 'r') as f:
        res = f.read()
    return res


def delete_blob(blob_name):
    os.remove(blob_name)


def exists_blob(blob_name):
    return os.path.isfile(blob_name)


def size_blob(blob_name):
    return os.path.getsize(blob_name)


def blob_list(blob_name=''):
    return os.listdir()