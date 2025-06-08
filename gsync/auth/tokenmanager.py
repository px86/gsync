"""Module for dealing with refresh and access tokens."""

import json
import logging
import os
import webbrowser
from datetime import datetime, timedelta
from typing import TypeAlias
import typing
import requests

from urllib.parse import urlencode
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
        self.client_creds = self.credreader.read()
        self.client_id = self.client_creds.web.client_id
        self.client_secret = self.client_creds.web.client_secret
        self.redirect_uri = None

    def refresh(self):
        """Refresh cached access token."""
        headers = {"content-type": "application/json"}
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }
        response = requests.post(
            self.api,
            headers=headers,
            json=payload,
        )
        if response.status_code == 200:
            data = json.loads(response.text)
            self._valid_till = (
                datetime.now() + timedelta(0, data["expires_in"]) - timedelta(0, 120)
            )
            self._access_token_cached = data["access_token"]
            logging.info(
                "access token refreshed is valid till %s", str(self._valid_till)
            )
        else:
            logging.critical(
                "failed to refresh access token, http_response: <%i> '%s' ",
                response.status_code,
                response.text,
            )
            raise TokenNotRefreshed()

    def get_access_token(self) -> str:
        """Return access token and refresh if necessary."""
        if datetime.now() >= self._valid_till:
            self.refresh()
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

    def auth(self) -> typing.Callable[[], str]:
        authcode = self.get_auth_code()
        tokens = self.exchange_auth_code(authcode)
        print(tokens)
        self.refresh_token = tokens["refresh_token"]
        self.refresh()
        return self.get_access_token
