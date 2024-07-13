from enum import Enum, auto
from shutil import copy
from pathlib import Path
from typing import Callable, Optional

from gi.repository import Gtk, Adw, GObject # type: ignore
from gettext import gettext as _

from .desktop_file import DesktopFile, DesktopEntry, Field
from .file_view import FileView
from .file_pool import TMP_POOL, USER_POOL


class FilePageState(Enum):
    EMPTY = auto()
    NEW_FILE = auto()
    LOADED_PINNED = auto()
    LOADED_SYSTEM = auto()


@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/file_page.ui')
class FilePage(Adw.Bin):
    __gtype_name__ = 'FilePage'

    window_title = Gtk.Template.Child()
    header_bar = Gtk.Template.Child()
    pin_button = Gtk.Template.Child()

    file_menu_button = Gtk.Template.Child()
    unpin_button = Gtk.Template.Child()
    rename_button = Gtk.Template.Child()
    duplicate_button = Gtk.Template.Child()

    toolbar_view = Gtk.Template.Child()
    file_view: Optional[FileView]
    
    file: Optional[DesktopFile] = None
    file_state = FilePageState.EMPTY
    banner_expanded = True

    def __init__(self):
        super().__init__()

        self.pin_button.connect('clicked', lambda _: self.pin_file())
        self.unpin_button.connect('clicked', lambda _: self.unpin_file())
        self.rename_button.connect('clicked', lambda _: self.rename_file())
        self.duplicate_button.connect('clicked', lambda _: self.duplicate_file())

    def pin_file(self):
        '''Copies a file to the user folder.'''
        match self.file_state:
            case FilePageState.LOADED_SYSTEM:
                pinned_path = USER_POOL.new_file_path(self.file.path.stem) # type: ignore
                self.file.save_as(pinned_path) # type: ignore
                self.load_file(DesktopFile(pinned_path))
            case _:
                raise ValueError(f'Cannot pin `DesktopFile` at "{self.file.path}", it is already pinned.') # type: ignore

    def on_leave(self, callback: 'Optional[Callable[[FilePage], None]]' = None):
        '''Called when the page is about to be closed, e.g. when `Escape` is pressed or when the app is closed'''
        match self.file_state:
            case FilePageState.EMPTY:
                if callback is not None:
                    callback(self)
            case FilePageState.NEW_FILE | FilePageState.LOADED_PINNED:
                self.file.save() # type: ignore
                USER_POOL.load()

                if callback is not None:
                    callback(self)
            case FilePageState.LOADED_SYSTEM:
                builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/file_page_dialogs.ui')

                dialog = builder.get_object('save_changes_dialog')

                def on_resp(widget, resp):
                    if resp == 'pin':
                        self.pin_file()
                    if resp == 'pin' or resp == 'discard':
                        if callback is not None:
                            callback(self)

                dialog.connect('response', on_resp)
                dialog.set_transient_for(self.get_root())
                dialog.present()

    def unpin_file(self):
        '''Deletes a pinned file.'''
        match self.file_state:
            case FilePageState.LOADED_PINNED:
                builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/file_page_dialogs.ui')

                dialog = builder.get_object('confirm_delete_dialog')

                def callback(widget, resp):
                    if resp == 'delete':
                        self.file.path.unlink() # type: ignore
                        USER_POOL.load()
                        self.emit('pop-request')

                dialog.connect('response', callback)
                dialog.set_transient_for(self.get_root())
                dialog.present()
            case _:
                raise ValueError(f'Cannot unpin `DesktopFile` at "{self.file.path}", it is not pinned.') # type: ignore

    def rename_file(self):
        match self.file_state:
            case FilePageState.NEW_FILE | FilePageState.LOADED_PINNED:
                builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/file_page_dialogs.ui')
                dialog = builder.get_object('rename_dialog')
                name_entry = builder.get_object('name_entry')
                name_entry.set_text(self.file.path.stem) # type: ignore
            case _:
                raise ValueError(f'Cannot rename `DesktopFile` at "{self.file.path}"') # type: ignore

        def get_new_path(name: str):
            match self.file_state:
                case FilePageState.NEW_FILE:
                    dir = TMP_POOL.default_dir
                case FilePageState.LOADED_PINNED:
                    dir = USER_POOL.default_dir

            return dir / Path(f'{Path(name)}.desktop')

        def path_is_valid() -> bool:
            name = name_entry.get_text()

            return '/' not in name and not get_new_path(name).exists()

        name_entry.connect('changed', lambda _: dialog.set_response_enabled(
            'rename',
            path_is_valid()
        ))

        def on_resp(widget, resp):
            if resp == 'rename':
                new_path = get_new_path(name_entry.get_text())

                if self.file.path.exists(): # type: ignore
                    self.file.save() # type: ignore
                    self.file.path.rename(new_path) # type: ignore
                    self.load_file(DesktopFile(new_path))
                else:
                    self.file.path = new_path # type: ignore

                USER_POOL.load()

        dialog.connect('response', on_resp)
        dialog.set_transient_for(self.get_root())
        dialog.show()

    def duplicate_file(self):
        assert self.file is not None

        new_path = USER_POOL.new_file_path(self.file.path.stem)

        copy(self.file.path, new_path)

        self.load_file(DesktopFile(new_path))
        USER_POOL.load()

    def load_file(self, file: DesktopFile, is_new = False):
        self.file = file

        if is_new:
            self.file_state = FilePageState.NEW_FILE
        elif file.pinned():
            self.file_state = FilePageState.LOADED_PINNED
        else:
            self.file_state = FilePageState.LOADED_SYSTEM

        file_view = FileView(file)
        self.toolbar_view.set_content(file_view)
        self.pin_button.set_visible(self.file_state != FilePageState.LOADED_PINNED)
        self.file_menu_button.set_visible(self.file_state != FilePageState.LOADED_SYSTEM)

        match self.file_state:
            case FilePageState.NEW_FILE:
                self.unpin_button.set_sensitive(False)
                self.duplicate_button.set_sensitive(False)
            case FilePageState.LOADED_PINNED | FilePageState.LOADED_SYSTEM:
                self.unpin_button.set_sensitive(True)
                self.duplicate_button.set_sensitive(True)
                self.window_title.set_title(self.file.get(DesktopEntry.NAME, '')) # type: ignore

        def update_title_visible(adjustment: Gtk.Adjustment):
            self.header_bar.set_show_title(adjustment.get_value() > 0)

        def update_title_text(file: DesktopFile, field: Field, value: str):
            if field == DesktopEntry.NAME:
                self.window_title.set_title(value)

        file_view.scrolled_window.get_vadjustment().connect('value-changed', update_title_visible)
        file.connect('field-set', update_title_text)

    """
    def _upload_icon(self):
        def callback(dialog, response):
            if response == Gtk.ResponseType.ACCEPT:
                path = Path(dialog.get_file().get_path())

                # Copy file inside app data directory, so it persists after reboot
                new_path = APP_DATA / 'icons' / path.name

                print(f'{path=}\n{new_path=}')

                copy(path, new_path)

                self.file.set(DesktopEntry.ICON, str(new_path))
                self.REMOVEME_update_icon()
                self.REMOVEMEupdate_page()

        dialog = Gtk.FileChooserNative(
            title=_('Upload icon'),
            action=Gtk.FileChooserAction.OPEN,
            accept_label=_('Open'),
            cancel_label=_('Cancel'))

        if (path := Path(self.file.get(DesktopEntry.ICON, ''))).exists():
            dialog.set_current_folder(Gio.File.new_for_path(str(path.parent)))

        dialog.connect('response', callback)
        dialog.set_modal(True)
        dialog.set_transient_for(self.get_root())
        dialog.show()
    """

GObject.signal_new('pop-request', FilePage, GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, ())
