"""Concrete implementation of google drive filesystem."""

from collections.abc import Iterable
from datetime import datetime, timezone

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

    def files(self, dirpath: str, recursive: bool) -> Iterable:
        """Return an iterator to iterate over files in the dirpath.

        If recursive is True, iterate recusively over subdirectories too.
        """
        return drive.walk_tree(dirpath, recursive)

    def last_modified_time(self, filepath: str) -> datetime:
        """Return the last modified time of the file a/c UTC timezone."""
        modified_time_str = drive.getprop(filepath, "modifiedTime")
        return datetime.fromisoformat(modified_time_str)

    def md5hash(self, filepath: str) -> str:
        """Return the md5 hash of the file as a string."""
        return drive.getprop(filepath, "md5Checksum")

    def size(self, filepath: str) -> int:
        """Return the size of the file in bytes."""
        return drive.getprop(filepath, "size")

    def touch(
        self,
        filepath: str,
        mtime: datetime | None = None,
    ):
        """Update the  modified timestam of given file.

        Defaults to current UTC time.
        """
        if mtime is None:
            mtime = datetime.now(tz=timezone.utc).isoformat()
        else:
            mtime = datetime.fromtimestamp(
                mtime.timestamp(), tz=timezone.utc
            ).isoformat()

        drive.update_metadata(filepath, {"modifiedTime": mtime})
