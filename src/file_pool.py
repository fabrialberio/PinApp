from gi.repository import GLib, Gio # type: ignore

from .config import *


def create_gfile_checked_samedir(path: str) -> Gio.File:
    for index in range(0, 999999):
        suffix = path.split('.')[-1]
        new_path = f'{path.removesuffix('.' + suffix)}{f'-{index}' if index > 0 else ''}.{suffix}'
        new_gfile = Gio.File.new_for_path(new_path)

        try:
            new_gfile.create(Gio.FileCreateFlags.NONE)
            return new_gfile
        except GLib.GError:
            continue

    raise IOError('Failed to create gfile after trying one million indexes.')

def create_gfile_checked(basename: str, parent: str) -> Gio.File:
    return create_gfile_checked_samedir(f'{parent}/{basename}')
