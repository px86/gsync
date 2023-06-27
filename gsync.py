#!/usr/bin/env python

import argparse
from gsync import sync


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="scan and sync files recursively"
    )
    parser.add_argument(
        "-c",
        "--checksum",
        action="store_true",
        help="use checksum instead of last modified time to compare files",
    )
    parser.add_argument("sourcedir")
    parser.add_argument("destinationdir")

    args = parser.parse_args()

    options = {
        "recursive": args.recursive,
        "checksum": args.checksum,
    }

    sync(args.sourcedir, args.destinationdir, options)


if __name__ == "__main__":
    main()
