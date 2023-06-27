"""Initialize a TokenManager object."""
from gsync.auth.tokenmanager import TokenManager
from gsync.gdrive.gdrive import GDrive, GDFileIterator


tokenmanager = TokenManager.from_env(
    client_id="CLIENT_ID",
    client_secret="CLIENT_SECRET",
    refresh_token="REFRESH_TOKEN",
)

drive = GDrive(tokenmanager.get_access_token)
drive.construct_tree()

__all__ = [
    "drive",
    "GDrive",
    "GDFileIterator",
]
