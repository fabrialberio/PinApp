from enum import Enum, auto
from typing import Callable, Optional

from gi.repository import Gtk, Adw, GObject, Gio # type: ignore
from gettext import gettext as _

from .desktop_file import DesktopFile, DesktopEntry, Field
from .file_view import FileView
from .file_pool import USER_POOL, USER_APPS, create_gfile_checked


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

    window_title = Gtk.Template.Child()
    header_bar = Gtk.Template.Child()
    pin_button = Gtk.Template.Child()

    file_menu_button = Gtk.Template.Child()
    unpin_button = Gtk.Template.Child()
    rename_button = Gtk.Template.Child()
    duplicate_button = Gtk.Template.Child()

    toolbar_view = Gtk.Template.Child()
    
    gfile: Optional[Gio.File] = None
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
            case FilePageState.NEW_FILE | FilePageState.LOADED_SYSTEM:
                pinned_gfile = create_gfile_checked(self.gfile.get_basename(), str(USER_APPS)) # type: ignore
                self.gfile.copy(pinned_gfile, Gio.FileCopyFlags.OVERWRITE) # type: ignore
                self.load_file(pinned_gfile)
            case _:
                raise ValueError(f'Cannot pin `DesktopFile` at "{self.gfile.get_path()}", it is already pinned.') # type: ignore

    def on_leave(self, callback: 'Optional[Callable[[FilePage], None]]' = None):
        '''Called when the page is about to be closed, e.g. when `Escape` is pressed or when the app is closed'''
        match self.file_state:
            case FilePageState.EMPTY:
                if callback is not None:
                    callback(self)
            case FilePageState.NEW_FILE | FilePageState.LOADED_PINNED:
                # TODO: If new file is not pinned, delete it from tmp
                self.file_view.save_file(self.gfile) # type: ignore
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
                    if resp == 'delete': # TODO: The file isn't actually deleted
                        self.gfile.delete() # type: ignore
                        USER_POOL.load()
                        self.emit('pop-request')

                dialog.connect('response', callback)
                dialog.set_transient_for(self.get_root())
                dialog.present()
            case _:
                raise ValueError(f'Cannot unpin `DesktopFile` at "{self.gfile.get_path()}", it is not pinned.') # type: ignore

    def rename_file(self):
        match self.file_state:
            case FilePageState.NEW_FILE | FilePageState.LOADED_PINNED:
                dialog = RenameFileDialog()
                dialog.name_entry.set_text(self.gfile.get_basename().removesuffix('.desktop')) # type: ignore
            case _:
                raise ValueError(f'Cannot rename `DesktopFile` at "{self.gfile.get_path()}"') # type: ignore

        def rename_path(name: str) -> str:
            return f'{self.gfile.get_parent().get_path()}/{name}.desktop' # type: ignore

        def path_is_valid() -> bool:
            name = dialog.name_entry.get_text()

            return '/' not in name and not Gio.File.new_for_path(rename_path(name)).query_exists()

        dialog.name_entry.connect('changed', lambda _: dialog.set_response_enabled(
            'rename',
            path_is_valid()
        ))

        def on_resp(widget, resp):
            if resp == 'rename':
                renamed_path = rename_path(dialog.name_entry.get_text())
                renamed_gfile = Gio.File.new_for_path(renamed_path)

                match self.file_state:
                    case FilePageState.NEW_FILE:
                        self.gfile = renamed_gfile
                    case FilePageState.LOADED_PINNED:
                        self.file_view.save_file(self.gfile) # type: ignore
                        self.gfile.move(renamed_gfile, Gio.FileCopyFlags.NONE) # type: ignore
                        self.load_file(renamed_gfile)

                USER_POOL.load()

        dialog.connect('response', on_resp)
        dialog.set_transient_for(self.get_root())
        dialog.show()

    def duplicate_file(self):
        new_gfile = create_gfile_checked(self.gfile.get_basename(), str(USER_APPS)) # type: ignore
        self.gfile.copy(new_gfile, Gio.FileCopyFlags.NONE) # type: ignore

        self.load_file(new_gfile)
        USER_POOL.load()

    def load_file(self, gfile: Gio.File, is_new = False):
        self.gfile = gfile
        desktop_file = DesktopFile.load_from_path(gfile.get_path())

        if is_new:
            self.file_state = FilePageState.NEW_FILE
        elif gfile.get_parent().get_path() == str(USER_APPS):
            self.file_state = FilePageState.LOADED_PINNED
        else:
            self.file_state = FilePageState.LOADED_SYSTEM

        self.file_view = FileView(desktop_file)
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

        def update_title_text(file: DesktopFile, field: Field, value: str):
            if field == DesktopEntry.NAME:
                self.window_title.set_title(value)

        self.file_view.scrolled_window.get_vadjustment().connect('value-changed', update_title_visible) # type: ignore
        desktop_file.connect('field-set', update_title_text)

    """
    def _upload_icon(self):
        def callback(dialog, response):
            if response == Gtk.ResponseType.ACCEPT:
                path = Path(dialog.get_file().get_path())

                # Copy file inside app data directory, so it persists after reboot
                new_path = APP_DATA / 'icons' / path.name

                print(f'{path=}\n{new_path=}')

                copy(path, new_path)

                self.file.set_str(DesktopEntry.ICON, str(new_path))
                self.REMOVEME_update_icon()
                self.REMOVEMEupdate_page()

        dialog = Gtk.FileChooserNative(
            title=_('Upload icon'),
            action=Gtk.FileChooserAction.OPEN,
            accept_label=_('Open'),
            cancel_label=_('Cancel'))

        if (path := Path(self.file.get_str(DesktopEntry.ICON))).exists():
            dialog.set_current_folder(Gio.File.new_for_path(str(path.parent)))

        dialog.connect('response', callback)
        dialog.set_modal(True)
        dialog.set_transient_for(self.get_root())
        dialog.show()
    """

GObject.signal_new('pop-request', FilePage, GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, ())
