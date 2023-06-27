from gsync.fs import FileSystem, GDFileSystem, LocalFileSystem


def sync(sourcedir: str, destinationdir: str):
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

    sync_dir(source, destination)


# FIXME: not implemented yet
def sync_dir(srcroot: FileSystem, destroot: FileSystem):
    """Sync the directories."""

    raise NotImplementedError()
    #
    # for sourcefile in srcroot.files(recurse=True):
    #     expected_destination_file = sourcefile.replace(srcroot.path, destroot.path)
    #     if not destroot.file_exists(expected_destination_file):
    #         # copy the file
    #         pass
    #     else:
    #         # compare the last modified timestamp and decide
    #         pass
