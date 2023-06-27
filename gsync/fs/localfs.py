"""Concrete implelemetaion for local filesystem."""

import os
from collections.abc import Iterable
from typing import BinaryIO

from gsync.fs.fs import FileSystem


class LocalFileIterator(Iterable):
    """An iterator class for iterating over the local file."""

    chunksize: int = 4096

    def __init__(self, file_object: BinaryIO):
        self.file_object = file_object

    def __iter__(self):
        for data in self.file_object.read(self.chunksize):
            yield data
        self.file_object.close()


class LocalFileSystem(FileSystem):
    """Concrete class representing local filesystem."""

    def exists(self, path: str) -> bool:
        "Check if given path exists."
        return os.path.exists(path)

    def mkdir(self, dirpath: str, mkparents: bool = True):
        """Create the given directory if it does not exist.

        If mkparents is True, also create the non-existent parents
        as necessary. Otherwise, raise an exception in such cases.
        """

    def copy_to(self, destination_path: str, source: Iterable):
        "Copy the contents from byte source to destination path."
        with open(destination_path, "wb") as fout:
            for data in source:
                fout.write(data)

    def ropen(self, filepath: str) -> Iterable:
        "Return a read only iterable object."
        return open(filepath, "rb")

    def files(self, dirpath: str, recursive: bool) -> Iterable:
        """Return an iterator to iterate over files in the dirpath.

        If recursive is True, iterate over subdirectories recursively.
        """
        yet_to_traverse = [dirpath]
        while len(yet_to_traverse) > 0:
            dirpath = yet_to_traverse.pop()
            entries = os.listdir(dirpath)
            for entry in entries:
                fullpath = os.path.join(dirpath, entry)
                if os.path.isdir(fullpath) and recursive:
                    yet_to_traverse.append(fullpath)
                else:
                    yield fullpath
