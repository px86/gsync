"""Initialize a TokenManager object."""

from gsync.auth.tokenmanager import TokenManager
from gsync.gdrive.gdrive import GDrive, GDFileIterator


tokenmanager = TokenManager()

drive = GDrive(tokenmanager.auth())
drive.construct_tree()

__all__ = [
    "drive",
    "GDrive",
    "GDFileIterator",
]
