import os
def related_file_path(input_file_path, prefix="", postfix="", replace_base=None, replace_ext=None):
    """
    For example: related_file_path("/path/to/file.ext", "a.", ".b")
     --> "/path/to/a.file.b.ext"
    """
    path, filename = os.path.split(input_file_path)

    # path = path/to
    # filename = file.ext

    basename, ext = os.path.splitext(filename)
    # basename = file
    # ext = .ext

    if replace_base is not None:
        basename = replace_base

    if replace_ext is not None:
        ext = replace_ext

    return os.path.join(path, "{}{}{}{}".format(prefix, basename, postfix, ext))
