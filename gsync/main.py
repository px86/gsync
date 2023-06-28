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

    return __sync(source, destination, options)


# TODO: add more customization options
def __sync(source: FileSystem, destination: FileSystem, options: dict):
    """Sync the directories."""

    for srcfile in source.files(source.root, options["recursive"]):
        prefix = os.path.commonprefix([source.root, srcfile])
        destfile = srcfile.replace(prefix, destination.root)

        print(f"{srcfile} -> {destfile}".ljust(120, " "), end=" ")

        if destination.exists(destfile):
            lmd_src = source.last_modified_time(srcfile)
            lmd_dest = destination.last_modified_time(destfile)
            if lmd_src > lmd_dest:
                print("UPDATING... (NOT IMPLEMENTED)")
                # TODO: implement this...
            elif lmd_src < lmd_dest:
                print("DEST NEWER...SKIPPING")
            else:
                print("UP-TO-DATE...SKIPPING")
        else:
            print("COPYING...")
            destination.copy_to(destfile, source.ropen(srcfile))
            destination.touch(destfile, source.last_modified_time(srcfile))
