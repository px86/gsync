"""Concrete implelemetaion for local filesystem."""

import os
import pathlib
import time
import hashlib
from datetime import datetime, timezone
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

    def __init__(self, root: str):
        self.root = root

    def exists(self, path: str) -> bool:
        "Check if given path exists."
        return os.path.exists(path)

    def mkdir(self, dirpath: str, mkparents: bool = True):
        """Create the given directory if it does not exist.

        If mkparents is True, also create the non-existent parents
        as necessary. Otherwise, raise an exception in such cases.
        """
        pathlib.Path(dirpath).mkdir(parents=mkparents, exist_ok=True)

    def copy_to(self, destination_path: str, source: Iterable):
        "Copy the contents from byte source to destination path."
        parentdir = os.path.dirname(destination_path)
        if not os.path.exists(parentdir):
            self.mkdir(parentdir)
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

    def last_modified_time(self, filepath: str) -> datetime:
        """Return the last modified time of the file a/c UTC timezone."""
        last_modified_time = os.stat(filepath).st_mtime + time.timezone
        return datetime.fromtimestamp(last_modified_time, tz=timezone.utc)

    def md5hash(self, filepath: str) -> str:
        """Return the md5 hash of the file as a string."""
        md5 = hashlib.md5()
        with open(filepath, "rb") as fin:
            while data := fin.read(4096):
                md5.update(data)
        return md5.hexdigest()

    def size(self, filepath: str) -> int:
        """Return the size of the file in bytes."""
        return os.stat(filepath).st_size

    def touch(
        self,
        filepath: str,
        mtime: datetime | None = None,
    ):
        """Update the modified timestamp of the given file.

        Defaults to the current UTC time.
        """
        if mtime is None:
            mtime = datetime.now(tz=timezone.utc).timestamp()
        else:
            mtime = mtime.timestamp()
        mtime -= time.timezone
        os.utime(filepath, (mtime, mtime))
