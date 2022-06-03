import os


def check_is_file_larger(file1, file2):
    return os.path.getsize(file1) > os.path.getsize(file2)
