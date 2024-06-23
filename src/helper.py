import os
import shutil


def path(filepath):
    return os.path.join(*filepath.split("/"))


def mkdir(filepath):
    filepath = path(filepath)
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    return filepath


def copyfile(source, destination):
    shutil.copyfile(source, destination)
