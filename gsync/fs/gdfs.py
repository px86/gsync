"""Concrete implementation of google drive filesystem."""

from collections.abc import Iterable

from gsync.fs.fs import FileSystem
from gsync.gdrive import drive, GDFileIterator


class GDFileSystem(FileSystem):
    """Class representing a google drive filesytem."""

    def __init__(self, root: str):
        self.root = root

    def exists(self, path: str) -> bool:
        "Check if given path exists."
        return drive.path_exists(path)[0]

    def mkdir(self, dirpath: str, mkparents: bool = True):
        """Create the given directory if it does not exist.

        If mkparents is True, also create the non-existent parents
        as necessary. Otherwise, raise an exception in such cases.
        """
        drive.mkdir(dirpath, mkparents)

    def copy_to(self, destination_path: str, source: Iterable):
        "Copy the contents from byte source to destination path."
        exists, gdfile = drive.path_exists(destination_path)
        if exists:
            assert gdfile["mimeType"] != "application/vnd.google-apps.folder"
            drive.update_content(gdfile["id"], source)
        else:
            drive.upload(destination_path, source)

    def ropen(self, filepath: str) -> GDFileIterator:
        "Return an read only io object, make sure to call close."
        return drive.open_read_only(filepath)
