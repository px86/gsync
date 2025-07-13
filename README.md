A cross platform CLI tool for synchronizing folders between google drive and local file-system (both ways).

NOTE: This is the development branch.

# Installation

## Step 0: Getting client credentials from Google Cloud Console

1. Create a poject in [google cloud console](https://console.cloud.google.com/).
2. Under `APIs and Services`, click on `OAuth Consent Screen`.
3. Enter application name, for example `yourname-gsync`. Fill in other details.
4. Once OAuth Consent Screen is configured, click on `Clients`, then click on `Create Client`.
5. Select Application Type as `Web Application`. Under `Authorized redirect URIs` fill some localhost addresses like `http://localhost:8121` etc.
6. Click on `Create` and download the `json` file. Rename this file as `client.json`.
7. On linux, put this file at `~/.config/gsync/client.json`. On windows, at `C:\Users\<Username>\AppData\Local\gsync\client.json`.

## Step 1: installing gsync

`gsync` uses `uv` to manage the project dependencies. You can find the steps to install `uv` [here](https://docs.astral.sh/uv/getting-started/installation/).

```
git clone https://github.com/px86/gsync
cd gsync
uv sync
uv run gsync.py --help
```

# Usage

`gsync` syncs file based on source and destination folders. For example, the below command will initialize a local copy of your google drive, into the `local-drive/` folder. Here the source is `gd:/` and `local-drive/` is the destination. -r means recursively.

  gsync gd:/  local-drive/ -r

Note that all google drive paths start with `gd:` prefix. `gd:/` refers to the `My Drive` folder in your google drive, `gd:/Documents/` will refer to `My Drive/Documents/` and so on.

You can switch the source and destination to sync in the reverse direction.

It is also possible to sync a given subdirectory only. For example, the below command will make sure that all files in the `local-drive/Documents/Work/` folder are present and up-to-date in the drive in `My Drive/Documents/` folder.

  gsync  local-drive/Documents/Work/  gd:/Documents/

## the --help option

```
usage: gsync.py [-h] [-r] [-c] [--dry-run] [--max-size SIZE] sourcedir destinationdir

positional arguments:
  sourcedir
  destinationdir

options:
  -h, --help       show this help message and exit
  -r, --recursive  sync source recursively
  -c, --checksum   use checksum instead of modified time and size to compare files
  --dry-run        only print the updates, do not do anything
  --max-size SIZE  skip files which are greater than SIZE bytes
```