"""Classes and functions for working with google drive API."""

import os
import logging
from collections.abc import Iterable
from typing import TypeAlias, Callable, Optional, TypedDict, Sequence

import requests

PathType: TypeAlias = str | bytes | os.PathLike
DrivePath: TypeAlias = str


class GDFileIterator(Iterable):
    """Class for iterating over the requests.Response object."""

    chunksize: int = 4096

    def __init__(self, response_object: requests.Response):
        self.response_object = response_object

    def __iter__(self):
        for data in self.response_object.iter_content(self.chunksize):
            yield data
        self.response_object.close()


class FileMetaData(TypedDict):
    """Important metadata about a file."""

    name: str
    id: str
    size: str
    mimeType: str
    parents: list[str]
    description: str
    createdTime: str
    modifiedTime: str
    md5Checksum: str
    trashed: bool


class GDrive:
    """Class exposing useful methods for working with google drive."""

    api = "https://www.googleapis.com/drive/v3"
    upload_api = "https://www.googleapis.com/upload/drive/v3"

    _folder_mimeType = "application/vnd.google-apps.folder"

    default_drive_fields = [
        "kind",
        "storageQuota",
        "driveThemes",
        "canCreateDrives",
        "importFormats",
        "exportFormats",
        "appInstalled",
        "user",
        "folderColorPalette",
        "maxImportSizes",
        "maxUploadSize",
        "teamDriveThemes",
        "canCreateTeamDrives",
    ]

    default_file_fields = list(FileMetaData.__annotations__.keys())

    def __init__(
        self, access_token_getter: Callable[[], str], path_prefix: str = "gd:"
    ):
        self.get_access_token = access_token_getter
        self.path_prefix = path_prefix

        self._tree_root = {}
        self._path_map = {}

        self.initialized = False

    def request(self, *args, **kwargs):
        """Proxy method for requests.request function call."""
        if "headers" in kwargs and "Authorization" not in kwargs["headers"]:
            kwargs["headers"].extend(
                {"Authorization": f"Bearer {self.get_access_token()}"}
            )
        else:
            kwargs["headers"] = {"Authorization": f"Bearer {self.get_access_token()}"}

        return requests.request(*args, **kwargs)

    def user_info(self) -> Optional[dict]:
        """Return authenticated user's details."""
        return self.about(fields=["user"])

    def about(self, fields: Optional[Sequence[str]] = None) -> Optional[dict]:
        """Return details about the drive."""
        if fields is None:
            fields = self.default_drive_fields

        response = self.request(
            method="GET",
            url=f"{self.api}/about",
            params={"fields": ",".join(fields)},
        )
        if response.status_code == 200:
            return response.json()
        return None

    def files(self, fields: Optional[Sequence[str]] = None) -> list[dict]:
        """Return a list of all files/folders in google drive.

        Return an empty list on error.
        """

        if not fields:
            fields = self.default_file_fields

        next_page_tok = None
        params = {"fields": f"files({','.join(fields)})"}

        files = []

        while True:
            if next_page_tok:
                params["pageToken"] = next_page_tok

            response = self.request(
                method="GET", url=f"{self.api}/files", params=params
            )
            if response.status_code == 200:
                data = response.json()
                files.extend(data["files"])
                next_page_tok = data.get("nextPageToken", None)
                if not next_page_tok:
                    break
            else:
                logging.error(
                    "could not fetch list of drive files,   "
                    "http_response: <%i> '%s'",
                    response.status_code,
                    response.text,
                )
                return []
        return files

    def file_info(
        self, id: str, fields: Optional[Sequence[str]] = None
    ) -> Optional[dict]:
        """Return inforamtion for the file with given id."""
        if fields is None:
            fields = self.default_file_fields
        response = self.request(
            method="GET",
            url=f"{self.api}/files/{id}",
            params={"fields": ",".join(fields)},
        )
        if response.status_code == 200:
            return response.json()
        logging.error(
            "could not fetch file info for id='%s', " "http_response: <%i> '%s'",
            id,
            response.status_code,
            response.text,
        )
        return None

    def download(self, gdpath: str, filepath: PathType):
        """Download file from google drive and save locally."""
        fin = self.open_read_only(gdpath)
        with open(filepath, "wb") as fout:
            for data in fin:
                fout.write(data)

    def open_read_only(self, path: str) -> GDFileIterator:
        """Open Google Drive file for reading.

        Make sure to close the requests.Response object.
        """
        assert self.initialized, "GDrive.construct_tree not called yet"

        file = self._path_map.get(path, None)
        if file is None:
            raise FileNotFoundError(f"{path} not found!")

        session = requests.Session()
        session.headers["Authorization"] = f"Bearer {self.get_access_token()}"
        response = session.get(
            f"{self.api}/files/{file['id']}",
            params={"alt": "media"},
            stream=True,
        )
        if response.status_code == 200:
            return GDFileIterator(response_object=response)
        raise IOError(f"file: {path} can not be opened for reading.")

    def create_folder(self, name: str, parentid: str = "root") -> dict | None:
        """Create a folder in google drive.

        If parentid is not provided, create the folder inside the
        'My Drive' folder of google drive.
        """
        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parentid],
        }
        response = self.request(
            method="POST",
            url=f"{self.api}/files",
            json=metadata,
        )
        if response.status_code == 200:
            folder = response.json()
            folder["subfolders"] = []
            folder["files"] = []
            return folder

        logging.error(
            "failed to create folder '%s' with parent='%s', http_response: <%i> '%s'",
            name,
            parentid,
            response.status_code,
            response.text,
        )
        return None

    def mkdir(self, path: str, mkparents: bool):
        """Make folder given by path.

        If mkparents is True, create all the missing parent folders.
        Otherwise throw an error if any of the parent folders is missing.
        """
        assert self.initialized, "GDrive.construct_tree not called yet"

        assert path != f"{self.path_prefix}/"

        pdirs, foldername = os.path.split(os.path.dirname(path))
        prefix, *pdirs = pdirs.split("/")

        assert prefix == self.path_prefix, "Path prefix did not match"

        last_node = self._tree_root

        for pdir in pdirs:
            found = False
            for subfolder in last_node["subfolders"]:
                if subfolder["name"] == pdir:
                    last_node = subfolder
                    found = True
                    break
            if not found:
                if mkparents:
                    folder = self.create_folder(pdir, last_node["id"])
                    if folder:
                        last_node["subfolders"].append(folder)
                        last_node = folder
                        continue
                raise FileNotFoundError(f"Parent folder: {pdir} not found!")

        # TODO: check if the folder exists already and raise FileExistsError
        folder = self.create_folder(foldername, last_node["id"])
        last_node["subfolders"].append(folder)
        self._path_map[path] = folder

        return folder

    def upload(self, destpath: str, source: Iterable) -> dict | None:
        """Upload file to google drive in a single step."""
        assert self.initialized, "GDrive.construct_tree not called yet"

        filename = os.path.basename(destpath)
        dirpath = os.path.dirname(destpath) + "/"

        if dirpath != "gd:/" and not self._path_map.get(dirpath, None):
            self.mkdir(dirpath, mkparents=True)

        parent = self._path_map.get(dirpath, None)
        if parent is None:
            raise FileNotFoundError(f"'{dirpath}' not foud!")

        # TODO: figure out file's mimeType
        metadata = {
            "name": filename,
            "parents": [parent["id"]],
        }
        response = self.request(
            method="POST",
            url=f"{self.upload_api}/files?uploadType=resumable",
            json=metadata,
        )
        resumable_uri = response.headers.get("Location", None)
        if not resumable_uri:
            logging.error(
                "for file '%s', "
                "resumable_uri not present in response header, "
                "http_response: <%i> '%s'",
                destpath,
                response.status_code,
                response.text,
            )
            return None

        # when using resumable_uri, we do not need the access_token in
        # request header, hence using requests.post directly
        response2 = requests.post(resumable_uri, data=source)
        if response2.status_code == 200:
            fileinfo = response2.json()
            self._path_map[destpath] = fileinfo
            return fileinfo

        logging.error(
            "failed to upload file '%s', with resumable_uri='%s', "
            "http_response: <%i> '%s'",
            destpath,
            resumable_uri,
            response2.status_code,
            response2.text,
        )
        return None

    def delete(self, id: str) -> bool:
        """Permanently delete file given by id."""
        response = self.request(
            method="DELETE",
            url=f"{self.api}/files/{id}",
        )
        # response body is empty on success
        if response.ok and response.text == "":
            return True
        return False

    def update_metadata(self, id: str, metadata: dict) -> bool:
        """Update file's metadata."""
        response = self.request(
            method="PATCH",
            url=f"{self.api}/files/{id}",
            json=metadata,
        )
        if response.status_code == 200:
            return True
        logging.error(
            "error while updating metadata for fileid '%s', "
            "http_response: <%i> '%s'",
            id,
            response.status_code,
            response.text,
        )
        return False

    def update_content(self, id: str, source: Iterable) -> bool:
        """Update file content."""
        response = self.request(
            method="PATCH",
            url=f"{self.upload_api}/files/{id}",
            param={"uploadType": "media"},
            data=source,
        )
        if response.status_code == 200:
            return True
        logging.error(
            "error while updating content for fileid '%s',  "
            "http_response: <%i> '%s'",
            id,
            response.status_code,
            response.text,
        )
        return False

    def empty_trash(self) -> bool:
        """Permanently delete all items from google drive trash."""
        response = self.request(method="DELETE", url=f"{self.api}/files/trash")
        if response.text == "":
            return True
        logging.error(
            "error while emptying trash, http_response: <%i> '%s'",
            response.status_code,
            response.text,
        )
        return False

    def search(self, query: str, fields: Optional[Sequence[str]] = None) -> list[dict]:
        """Perform a query on files API endpoint."""

        if not fields:
            fields = self.default_file_fields

        next_page_tok = None
        params = {
            "q": query,
            "fields": f"files({','.join(fields)})",
        }

        files = []
        while True:
            if next_page_tok:
                params["pageToken"] = next_page_tok

            response = self.request(
                method="GET", url=f"{self.api}/files", params=params
            )
            if response.status_code == 200:
                data = response.json()
                files.extend(data["files"])
                next_page_tok = data.get("nextPageToken", None)
                if not next_page_tok:
                    break
            else:
                logging.error(
                    "error while emptying trash, http_response: <%i> '%s'",
                    response.status_code,
                    response.text,
                )
        return files

    def construct_tree(self) -> None:
        """Create a tree data structure replicating drive's folder structure.

        The root of the tree represents the 'My Drive' (root) folder. Each node
        (a dict type) has id, name, files(list), and subfolders(list)
        properties (key). The subfolders are themselves a node in the tree and
        recursively list their subfolders.
        """
        files = self.files()
        folders = [
            f for f in files if f["mimeType"] == "application/vnd.google-apps.folder"
        ]

        fentries = {
            folder["id"]: [f for f in files if f["parents"] == [folder["id"]]]
            for folder in folders
        }

        root_info = self.file_info("root", ["name", "id"])
        assert root_info is not None
        root_content = [f for f in files if f["parents"] == [root_info["id"]]]
        fentries["root"] = fentries[root_info["id"]] = root_content

        path_map = {}
        path_map["gd:/"] = root_info

        def recursively_fill_nodes(node, parentpath: str):
            currpath = f"{parentpath}{node['name']}/" if parentpath else "gd:/"
            node["path"] = currpath
            node["files"] = []
            node["subfolders"] = []
            path_map[currpath] = node
            for entry in fentries[node["id"]]:
                if entry["mimeType"] == "application/vnd.google-apps.folder":
                    subfolder = recursively_fill_nodes(entry, currpath)
                    node["subfolders"].append(subfolder)
                else:
                    node["files"].append(entry)
                    path = currpath + entry["name"]
                    entry["path"] = path
                    path_map[path] = entry
            return node

        self._tree_root = recursively_fill_nodes(root_info, "")
        self._path_map = path_map
        self.initialized = True

    # TODO: Simplify this method.
    def path_exists(self, gdpath: str) -> tuple[bool, dict]:
        """Check if the given path exists on google drive.

        Argument gdpath must start with the gd: prefix.
        For example, the gdpath 'gd:/foo/bar.txt' represents a file 'bar.txt'
        inside the 'foo' folder, inside the root folder ('My Drive') of google
        drive.

        A tuple of size two is returned, where the first element is a bool,
        indicating if the path exists or not.

        If the path exists, the second element in the returned tuple contains
        basic details about the matched file/folder.

        If the path does not exist, the second element of the returned tuple
        contains the id, and name of the last matched node, and also the
        remaining part of the given path which was not matched.
        """
        assert self.initialized, "GDrive.construct_tree not called yet"

        prefix, *dirs, filename = gdpath.split("/")

        assert prefix == self.path_prefix, "Path prefix do not match"

        last_matched_node = self._tree_root
        matched_so_far = True

        indx = 0
        for indx, dir in enumerate(dirs):
            dir_matched = False
            for subfolder in last_matched_node["subfolders"]:
                if dir == subfolder["name"]:
                    last_matched_node = subfolder
                    dir_matched = True
                    break
            if not dir_matched:
                matched_so_far = False
                mismatch = "/".join(gdpath.split("/")[indx + 1 :])
                break

        if matched_so_far and filename:
            for file in last_matched_node["files"]:
                if filename == file["name"]:
                    return True, file
            matched_so_far = False
            mismatch = filename

        elif matched_so_far:
            return True, last_matched_node

        return False, {
            "last_matched_id": last_matched_node["id"],
            "last_matched_name": last_matched_node["name"],
            "mismatch": mismatch,
        }

    def walk_tree(self, dirpath: str, recursive: bool = True) -> Iterable:
        """Walk down the filetree."""
        assert self.initialized, "GDrive.construct_tree not called yet"

        node = self._path_map.get(dirpath, None)
        if node is None:
            raise FileNotFoundError(f"'{dirpath}' not found")

        yet_to_traverse = [node]
        while len(yet_to_traverse) > 0:
            node = yet_to_traverse.pop()
            for file in node["files"]:
                yield file["path"]
            if recursive:
                yet_to_traverse.extend(node["subfolders"])

    def getprop(self, path: str, prop: str):
        """Get 'prop' property for node associated with path."""
        assert self.initialized, "GDrive.construct_tree not called yet"

        node = self._path_map.get(path, None)
        if node is None:
            raise FileNotFoundError(f"'{path}' not found!")

        # let keyerror be raised if prop does not exist in node.
        return node[prop]
