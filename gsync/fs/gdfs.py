"""Implementation of filesystem abstractions for google drive."""

from collections.abc import Iterable
from datetime import datetime, timezone

from gsync.fs.fs import FileSystem
from gsync.gdrive import drive, GDFileIterator


class GDFileSystem(FileSystem):
    """Implementation of necessary filesystem operations for google drive."""

    def __init__(self, root: str):
        self.root = root

    def exists(self, path: str) -> bool:
        "Check if the given path exists."
        return drive.path_exists(path)[0]

    def mkdir(self, dirpath: str, mkparents: bool = True):
        """Create the given directory if it does not exist.

        If mkparents is True, also create the non-existent parents
        as necessary. Otherwise, raise an exception in such cases.
        """
        drive.mkdir(dirpath, mkparents)

    def copy_to(self, destination_path: str, source: Iterable):
        """Copy the contents from byte source to destination file.

        If the destination file does not exist already, create one.
        Otherwise update the content of file.
        """
        exists, _ = drive.path_exists(destination_path)
        if exists:
            drive.update_content(destination_path, source)
        else:
            drive.upload(destination_path, source)

    def ropen(self, filepath: str) -> GDFileIterator:
        """Return an read only io object, make sure to call close."""
        return drive.open_read_only(filepath)

    def files(self, dirpath: str, recursive: bool) -> Iterable:
        """Return an iterator to iterate over files in 'dirpath'.

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
        """Update the modified timestamp of the given file.

        Defaults to current UTC time.
        """
        if mtime is None:
            mtime = datetime.now(tz=timezone.utc).isoformat()
        else:
            mtime = datetime.fromtimestamp(
                mtime.timestamp(), tz=timezone.utc
            ).isoformat()

        drive.update_metadata(filepath, {"modifiedTime": mtime})
