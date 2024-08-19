from enum import Enum, auto
from typing import Callable, Optional

from gi.repository import Gtk, Adw, GObject, Gio # type: ignore
from gettext import gettext as _

from .desktop_file import DesktopFile, DesktopEntry, Field
from .file_view import FileView
from .config import USER_APPS
from .file_pool import create_gfile_checked


class FilePageState(Enum):
    EMPTY = auto()
    NEW_FILE = auto()
    LOADED_PINNED = auto()
    LOADED_SYSTEM = auto()


@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/dialog_rename_file.ui')
class RenameFileDialog(Adw.MessageDialog):
    __gtype_name__ = 'RenameFileDialog'

    name_entry = Gtk.Template.Child()


@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/file_page.ui')
class FilePage(Adw.Bin):
    __gtype_name__ = 'FilePage'

    gfile: Optional[Gio.File] = None
    desktop_file: DesktopFile
    file_state = FilePageState.EMPTY

    window_title = Gtk.Template.Child()
    header_bar = Gtk.Template.Child()
    file_menu_button = Gtk.Template.Child()
    pin_button = Gtk.Template.Child()
    unpin_button = Gtk.Template.Child()
    rename_button = Gtk.Template.Child()
    duplicate_button = Gtk.Template.Child()
    toolbar_view = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        self.pin_button.connect('clicked', self._pin_file)
        self.unpin_button.connect('clicked', self._unpin_file)
        self.rename_button.connect('clicked', self._rename_file)
        self.duplicate_button.connect('clicked', self._duplicate_file)

    def set_file(self, gfile: Gio.File, desktop_file: DesktopFile, is_new = False):
        self.gfile = gfile
        self.desktop_file = desktop_file

        if is_new:
            self.file_state = FilePageState.NEW_FILE
        elif gfile.get_parent().get_path() == str(USER_APPS):
            self.file_state = FilePageState.LOADED_PINNED
        else:
            self.file_state = FilePageState.LOADED_SYSTEM

        self.file_view = FileView(self.desktop_file)
        self.toolbar_view.set_content(self.file_view)
        self.pin_button.set_visible(self.file_state != FilePageState.LOADED_PINNED)
        self.file_menu_button.set_visible(self.file_state != FilePageState.LOADED_SYSTEM)

        match self.file_state:
            case FilePageState.NEW_FILE:
                self.unpin_button.set_sensitive(False)
                self.duplicate_button.set_sensitive(False)
            case FilePageState.LOADED_PINNED | FilePageState.LOADED_SYSTEM:
                self.unpin_button.set_sensitive(True)
                self.duplicate_button.set_sensitive(True)
                self.window_title.set_title(self.file_view.file.get_str(DesktopEntry.NAME)) # type: ignore

        def update_title_visible(adjustment: Gtk.Adjustment):
            self.header_bar.set_show_title(adjustment.get_value() > 0)

        def update_title_text(_file: DesktopFile, field: Field, value: str):
            if field == DesktopEntry.NAME:
                self.window_title.set_title(value)

        self.file_view.scrolled_window.get_vadjustment().connect('value-changed', update_title_visible) # type: ignore
        self.desktop_file.connect('field-set', update_title_text)

    def _pin_file(self, _button: Optional[Gtk.Button] = None):
        '''Copies a file to the user folder.'''
        match self.file_state:
            case FilePageState.NEW_FILE | FilePageState.LOADED_SYSTEM:
                pinned_gfile = create_gfile_checked(self.gfile.get_basename(), str(USER_APPS)) # type: ignore
                self.gfile.copy(pinned_gfile, Gio.FileCopyFlags.OVERWRITE) # type: ignore
                self.set_file(pinned_gfile, self.desktop_file)
            case _:
                raise ValueError(f'Cannot pin `DesktopFile` at "{self.gfile.get_path()}", it is already pinned.') # type: ignore

    def _unpin_file(self, _button: Optional[Gtk.Button] = None):
        '''Deletes a pinned file.'''
        match self.file_state:
            case FilePageState.LOADED_PINNED:
                builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/file_page_dialogs.ui')
                dialog = builder.get_object('confirm_delete_dialog')

                def on_response(_dialog: Adw.MessageDialog, response: str):
                    if response == 'delete': # TODO: The file isn't actually deleted
                        self.gfile.delete() # type: ignore
                        self.emit('pop-request')

                dialog.connect('response', on_response)
                dialog.set_transient_for(self.get_root())
                dialog.present()
            case _:
                raise ValueError(f'Cannot unpin `DesktopFile` at "{self.gfile.get_path()}", it is not pinned.') # type: ignore

    def _rename_file(self, _button: Optional[Gtk.Button] = None):
        match self.file_state:
            case FilePageState.NEW_FILE | FilePageState.LOADED_PINNED:
                dialog = RenameFileDialog()
                dialog.name_entry.set_text(self.gfile.get_basename().removesuffix('.desktop')) # type: ignore
            case _:
                raise ValueError(f'Cannot rename `DesktopFile` at "{self.gfile.get_path()}"') # type: ignore

        def rename_path(name: str) -> str:
            return f'{self.gfile.get_parent().get_path()}/{name}.desktop' # type: ignore

        def on_name_changed(_entry: Adw.EntryRow):
            name = dialog.name_entry.get_text()

            dialog.set_response_enabled(
                'rename',
                not ('/' in name or Gio.File.new_for_path(rename_path(name)).query_exists())
            )

        dialog.name_entry.connect('changed', on_name_changed)

        def on_response(_dialog: RenameFileDialog, response: str):
            if response == 'rename':
                renamed_path = rename_path(dialog.name_entry.get_text())
                renamed_gfile = Gio.File.new_for_path(renamed_path)

                match self.file_state:
                    case FilePageState.NEW_FILE:
                        self.gfile = renamed_gfile
                    case FilePageState.LOADED_PINNED:
                        self.file_view.save_file(self.gfile) # type: ignore
                        self.gfile.move(renamed_gfile, Gio.FileCopyFlags.NONE) # type: ignore
                        self.set_file(renamed_gfile, self.desktop_file)

        dialog.connect('response', on_response)
        dialog.set_transient_for(self.get_root())
        dialog.show()

    def _duplicate_file(self, _button: Optional[Gtk.Button] = None):
        new_gfile = create_gfile_checked(self.gfile.get_basename(), str(USER_APPS)) # type: ignore
        self.gfile.copy(new_gfile, Gio.FileCopyFlags.OVERWRITE) # type: ignore
        self.set_file(new_gfile, self.desktop_file)

    def on_leave(self, callback: 'Optional[Callable[[FilePage], None]]' = None):
        '''Called when the page is about to be closed, e.g. when `Escape` is pressed or when the app is closed'''
        match self.file_state:
            case FilePageState.EMPTY:
                if callback is not None:
                    callback(self)
            case FilePageState.NEW_FILE | FilePageState.LOADED_PINNED:
                # TODO: If new file is not pinned, delete it from tmp
                self.file_view.save_file(self.gfile) # type: ignore

                if callback is not None:
                    callback(self)
            case FilePageState.LOADED_SYSTEM:
                builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/file_page_dialogs.ui')

                dialog = builder.get_object('save_changes_dialog')

                def on_response(_dialog: Adw.MessageDialog, response: str):
                    if response == 'pin':
                        self._pin_file()
                    if response == 'pin' or response == 'discard':
                        if callback is not None:
                            callback(self)

                dialog.connect('response', on_response)
                dialog.set_transient_for(self.get_root())
                dialog.present()

GObject.signal_new('pop-request', FilePage, GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, ())
