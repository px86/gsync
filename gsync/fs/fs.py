"""Abstraction over necessary filesystem functionalities."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime


class FileSystem(ABC):
    """An abstract class representing necessary filesystem operations."""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if given path exists."""

    @abstractmethod
    def mkdir(self, dirpath: str, mkparents: bool = True):
        """Create the given directory if it does not exist.

        If mkparents is True, also create the non-existent parents
        as necessary. Otherwise, raise an exception in such cases.
        """

    @abstractmethod
    def copy_to(self, destination_path: str, source: Iterable):
        """Copy the contents from byte source to destination path.

        Implementations should deal with cases where the destination
        does or does not exist.
        """

    @abstractmethod
    def ropen(self, filepath: str) -> Iterable:
        """Open a file for reading and return an iterable."""

    @abstractmethod
    def files(self, dirpath: str, recursive: bool) -> Iterable:
        """Return an iterator to iterate over files in the dirpath.

        If recursive is True, iterate recusively over subdirectories too.
        """

    @abstractmethod
    def last_modified_time(self, filepath: str) -> datetime:
        """Return the last modified time of the file a/c UTC timezone."""

    @abstractmethod
    def md5hash(self, filepath: str) -> str:
        """Return the md5 hash of the file as a string."""

    @abstractmethod
    def size(self, filepath: str) -> int:
        """Return the size of the file in bytes."""

    @abstractmethod
    def touch(
        self,
        filepath: str,
        mtime: datetime | None = None,
    ):
        """Update the modified timestamp of the given file.

        Defaults to the current UTC time.
        """
