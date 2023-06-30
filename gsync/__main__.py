import argparse

from gsync.sync import sync, Options


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="sync source recursively"
    )
    parser.add_argument(
        "-c",
        "--checksum",
        action="store_true",
        help="use checksum instead of modified time and size to compare files",
    )
    # TODO: implement this
    # parser.add_argument(
    #     "--clean-destination",
    #     action="store_true",
    #     help="delete files from destination that are not in source",
    # )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="only print the updates, do not do anything",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        metavar="SIZE",
        help="skip files which are greater than SIZE bytes",
    )

    parser.add_argument("sourcedir")
    parser.add_argument("destinationdir")

    args = parser.parse_args()

    options: Options = {
        "recursive": args.recursive,
        "checksum": args.checksum,
        "maxsize": args.max_size,
        "dryrun": args.dry_run,
        # "cleandest": args.clean_destination,
    }

    sync(args.sourcedir, args.destinationdir, options)


if __name__ == "__main__":
    main()
