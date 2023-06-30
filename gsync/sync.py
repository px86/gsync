import os
from gsync.fs import FileSystem, GDFileSystem, LocalFileSystem
from typing import TypedDict


class Options(TypedDict):
    """Supported options by gsync."""

    recursive: bool
    checksum: bool
    dryrun: bool
    maxsize: int
    # cleandest: bool


def sync(sourcedir: str, destinationdir: str, options: dict):
    """Sync the destination with the source."""
    source = (
        GDFileSystem(sourcedir)
        if sourcedir.startswith("gd:")
        else LocalFileSystem(sourcedir)
    )
    destination = (
        GDFileSystem(destinationdir)
        if destinationdir.startswith("gd:")
        else LocalFileSystem(destinationdir)
    )

    return __sync(source, destination, options)


def __sync(source: FileSystem, destination: FileSystem, options: dict):
    def copy(msg: str, destfile: str, srcfile: str):
        print(msg)
        if not options["dryrun"]:
            destination.copy_to(destfile, source.ropen(srcfile))
            destination.touch(destfile, source.last_modified_time(srcfile))

    for srcfile in source.files(source.root, options["recursive"]):
        prefix = os.path.commonprefix([source.root, srcfile])
        destfile = srcfile.replace(prefix, destination.root)

        print(f"{srcfile} ==> {destfile}".ljust(120, " "), end=" ")

        if maxsize := options.get("maxsize"):
            size_src = source.size(srcfile)
            if size_src > maxsize:
                print("TOO BIG...SKIPPING")
                continue

        if not destination.exists(destfile):
            copy("COPYING...", destfile, srcfile)

        else:
            if options["checksum"]:
                # compare files by thier md5 hashes
                cksum_src = source.md5hash(srcfile)
                cksum_dest = destination.md5hash(destfile)
                if cksum_src == cksum_dest:
                    print("CHECKSUM MATCHED...SKIPPING")
                else:
                    copy("UPDATING...", destfile, srcfile)
            else:
                # compare files by thier modified time and file sizes
                lmd_src = source.last_modified_time(srcfile)
                lmd_dest = destination.last_modified_time(destfile)

                if lmd_src > lmd_dest:
                    print(f"{lmd_src=}, {lmd_dest=}")
                    copy("UPDATING...", destfile, srcfile)
                elif lmd_src < lmd_dest:
                    print("DEST NEWER...SKIPPING")
                else:
                    size_src = source.size(srcfile)
                    size_dest = destination.size(destfile)
                    if size_src == size_dest:
                        print("UP-TO-DATE...SKIPPING")
                    else:
                        copy("UPDATING...", destfile, srcfile)

    if options["dryrun"]:
        print("")
        print("Dry Run only. Nothing changed.")
