"""Module for dealing with refresh and access tokens."""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import TypeAlias

import requests

PathType: TypeAlias = str | bytes | os.PathLike


class TokenNotRefreshed(Exception):
    """Exception thrown when access token can not be refreshed."""


class EnvironmentVariableNotSet(Exception):
    """Exception thrown when an expected environment variable is not set."""


class TokenManager:
    """Class for managing and refreshing access token."""

    api = "https://oauth2.googleapis.com/token"

    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.refresh()

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
            logging.info("access token refreshed is valid till %s", str(self._valid_till))
        else:
            logging.critical(
                "failed to refresh access token, http_response: <%i> '%s' ",
                response.status_code, response.text
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
    def from_env(cls,
        client_id: str, client_secret: str, refresh_token: str
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
