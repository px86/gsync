"""Module for reading client credentials json file."""

import os
import json
from dataclasses import dataclass
from platformdirs import user_config_dir

PathType = str | bytes | os.PathLike


@dataclass
class WebCredentials:
    client_id: str
    client_secret: str
    project_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    redirect_uris: list[str]


@dataclass
class ClientCredentials:
    web: WebCredentials


class CredentialsReader:
    """Read client credentials json file."""

    def __init__(self, path: PathType = None) -> None:
        if path is None:
            self.path = os.path.join(user_config_dir(), "gsync", "client.json")
        else:
            self.path = path

    def read(self) -> ClientCredentials:
        with open(self.path, "rt") as f:
            data = json.loads(f.read())
            web = WebCredentials(**data["web"])
            return ClientCredentials(web)


if __name__ == "__main__":
    cr = CredentialsReader()
    print(cr.read())
