"""Abstraction over filesystem functionalities."""

from abc import ABC, abstractmethod
from collections.abc import Iterable


class FileSystem(ABC):
    """An abstract class representing a file."""

    @abstractmethod
    def exists(self, path: str) -> bool:
        "Check if given path exists."

    @abstractmethod
    def mkdir(self, dirpath: str, mkparents: bool = True):
        """Create the given directory if it does not exist.

        If mkparents is True, also create the non-existent parents
        as necessary. Otherwise, raise an exception in such cases.
        """

    @abstractmethod
    def copy_to(self, destination_path: str, source: Iterable):
        "Copy the contents from byte source to destination path."

    @abstractmethod
    def ropen(self, filepath: str) -> Iterable:
        "Open a file for reading and return an iterable."

    @abstractmethod
    def files(self, dirpath: str, recursive: bool) -> Iterable:
        """Return an iterator to iterate over files in the dirpath.

        If recursive is True, iterate recusively over subdirectories too.
        """
