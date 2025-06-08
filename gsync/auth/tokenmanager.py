"""Module for dealing with refresh and access tokens."""

import json
import logging
import os
import typing
import webbrowser
from datetime import datetime, timedelta
from typing import TypeAlias
from urllib.parse import urlencode

import requests
from platformdirs import user_cache_dir

from gsync.auth.credreader import CredentialsReader, ClientCredentials
from gsync.auth.server import select_redirect_uri, launch_server

PathType: TypeAlias = str | bytes | os.PathLike


class TokenNotRefreshed(Exception):
    """Exception thrown when access token can not be refreshed."""


class EnvironmentVariableNotSet(Exception):
    """Exception thrown when an expected environment variable is not set."""


class TokenManager:
    """Class for managing and refreshing access token."""

    api = "https://oauth2.googleapis.com/token"

    def __init__(self, credreader: CredentialsReader | None = None):
        self.credreader = CredentialsReader() if credreader is None else credreader
        self.cachefile = os.path.join(user_cache_dir(), "gsync", "token.json")
        self.client_creds = self.credreader.read()
        self.client_id = self.client_creds.web.client_id
        self.client_secret = self.client_creds.web.client_secret
        self.redirect_uri = None

    def read_cache_file(self) -> dict:
        with open(self.cachefile, "r") as f:
            return json.loads(f.read())

    def write_cache_file(self, data: dict) -> None:
        with open(self.cachefile, "w") as f:
            f.write(json.dumps(data))

    def is_refresh_token_valid(self, refresh_token: str) -> bool:
        "Check the validity of refresh token."
        data = self.token_refresh(refresh_token)
        return data is not None

    def token_refresh(self, refresh_token: str) -> dict | None:
        """Refresh cached access token."""
        headers = {"content-type": "application/json"}
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        response = requests.post(
            self.api,
            headers=headers,
            json=payload,
        )
        if response.status_code == 200:
            data = response.json()
            self._valid_till = (
                datetime.now() + timedelta(0, data["expires_in"]) - timedelta(0, 120)
            )
            self._access_token_cached = data["access_token"]
            logging.info(
                "access token refreshed is valid till %s", str(self._valid_till)
            )
            return data
        else:
            logging.critical(
                "failed to refresh access token, http_response: <%i> '%s' ",
                response.status_code,
                response.text,
            )
            return None

    def get_access_token(self) -> str:
        """Return access token and refresh if necessary."""
        if datetime.now() >= self._valid_till:
            self.token_refresh(self.refresh_token)
        return self._access_token_cached

    @property
    def access_token(self) -> str:
        """Return access token and refresh if necessary."""
        return self.get_access_token()

    @classmethod
    def from_env(
        cls, client_id: str, client_secret: str, refresh_token: str
    ) -> "TokenManager":
        """Read secrets from environment variables and construct a TokenManager object."""
        try:
            return TokenManager(
                client_id=os.environ[client_id],
                client_secret=os.environ[client_secret],
                refresh_token=os.environ[refresh_token],
            )
        except KeyError as keyerror:
            raise EnvironmentVariableNotSet() from keyerror

    def get_auth_code(self) -> str:
        uri = select_redirect_uri(self.client_creds.web.redirect_uris)
        self.redirect_uri = uri.geturl()
        _, authcode_cb = launch_server(port=uri.port)
        params = {
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "scope": "https://www.googleapis.com/auth/drive",
            "response_type": "code",
            "prompt": "consent",
            "access_type": "offline",
        }
        authurl = self.client_creds.web.auth_uri + "?" + urlencode(params)
        print(f"Visit the following URL in a web browser\n\n{authurl}")
        webbrowser.open(authurl)
        return authcode_cb()

    def exchange_auth_code(self, authcode: str) -> dict | None:
        """Exchange auth code for access and refresh tokens."""

        payload = {
            "code": authcode,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
        }
        response = requests.post(self.client_creds.web.token_uri, data=payload)
        if response.ok:
            return response.json()
        return None

    def authenticate(self) -> typing.Callable[[], str]:
        cached_data = self.read_cache_file()
        if "refresh_token" in cached_data and self.is_refresh_token_valid(
            cached_data["refresh_token"]
        ):
            self.refresh_token = cached_data["refresh_token"]
        else:
            authcode = self.get_auth_code()
            tokens = self.exchange_auth_code(authcode)
            self.refresh_token = tokens["refresh_token"]
            self.write_cache_file(tokens)
            self.token_refresh(self.refresh_token)
        return self.get_access_token
