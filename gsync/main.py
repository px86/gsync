import os
from gsync.fs import FileSystem, GDFileSystem, LocalFileSystem


def sync(sourcedir: str, destinationdir: str, options: dict):
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

    return sync_dir(source, destination, options)


def sync_dir(source: FileSystem, destination: FileSystem, options: dict):
    """Sync the directories."""

    for srcfile in source.files(source.root, options["recursive"]):
        prefix = os.path.commonprefix([source.root, srcfile])
        destfile = srcfile.replace(prefix, destination.root)

        print(f"{srcfile} -> {destfile}", end=" ")

        # TODO: figure out how to preseve timestamps when writing files
        #       from local filesytem to google-drive and vice versa
        if destination.exists(destfile):
            lmd_src = source.last_modified_time(srcfile)
            lmd_dest = destination.last_modified_time(destfile)
            if lmd_src > lmd_dest:
                print("UPDATE (NOT IMPLEMENTED)")
            else:
                print("destination file is newer, skipping...")
        else:
            print("DOES NOT EXIST...COPYING")
            destination.copy_to(destfile, source.ropen(srcfile))
