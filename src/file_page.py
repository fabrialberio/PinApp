from shutil import copy
from pathlib import Path
from typing import Callable, Optional

from gi.repository import Gtk, Adw, GObject # type: ignore
from gettext import gettext as _

from .desktop_file import DesktopFile, DesktopEntry, Field
from .file_view import FileView
from .file_pool import USER_POOL


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
    
    banner_expanded = True
    file: DesktopFile

    @property
    def allow_leave(self) -> bool:
        if self.file is not None:
            return not self.file.edited()
        else:
            return True


    def __init__(self):
        super().__init__()

        self.file = None

        self.pin_button.connect('clicked', lambda _: self.pin_file())
        self.unpin_button.connect('clicked', lambda _: self.unpin_file())
        self.rename_button.connect('clicked', lambda _: self.rename_file())
        self.duplicate_button.connect('clicked', lambda _: self.duplicate_file())

    def pin_file(self):
        '''Saves a file to the user folder. Used when the file does not exist or it does not have write access.'''
        assert self.file is not None

        is_new_file = not self.file.path.exists()
        pinned_path = USER_POOL.new_file_path(self.file.path.stem)

        self.file.save_as(pinned_path)
        self.emit('file-changed')

        if is_new_file:
            self.emit('file-leave')
        else:
            self.load_path(pinned_path)

    def on_leave(self, callback: 'Optional[Callable[[FilePage], None]]' = None):
        '''Called when the page is about to be closed, e.g. when `Escape` is pressed or when the app is closed'''
        if self.allow_leave or self.file is None:
            self.emit('file-leave')
            if callback is not None:
                callback(self)
        else:
            if self.file.path.exists():
                self.file.save()
                self.emit('file-changed')
                self.emit('file-leave')

                if callback is not None:
                    callback(self)
            else:
                builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/file_page_dialogs.ui')

                dialog = builder.get_object('save_changes_dialog')

                def on_resp(widget, resp):
                    if resp == 'discard':
                        self.emit('file-leave')
                        if callback is not None:
                            callback(self)
                    elif resp == 'pin':
                        self.pin_file()
                        if callback is not None:
                            callback(self)

                dialog.connect('response', on_resp)
                dialog.set_transient_for(self.get_root())
                dialog.present()

    def unpin_file(self):
        '''Deletes a file. It is used when the file has write access.'''
        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/file_page_dialogs.ui')
        
        dialog = builder.get_object('confirm_delete_dialog')

        def callback(widget, resp):
            if resp == 'delete':
                self.file.path.unlink()
                self.emit('file-leave')
                self.emit('file-changed')

        dialog.connect('response', callback)
        dialog.set_transient_for(self.get_root())
        dialog.present()

    def rename_file(self):
        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/file_page_dialogs.ui')
        dialog = builder.get_object('rename_dialog')
        name_entry = builder.get_object('name_entry')
        name_entry.set_text(self.file.path.stem)

        def get_path():
            return USER_POOL.default_dir / Path(f'{Path(name_entry.get_text())}.desktop')

        def path_is_valid() -> bool:
            path = name_entry.get_text()

            return '/' not in path and not get_path().exists()

        name_entry.connect('changed', lambda _: dialog.set_response_enabled(
            'rename',
            path_is_valid()
        ))

        def on_resp(widget, resp):
            if resp == 'rename':
                new_path = get_path()

                if self.file.path.exists():
                    self.file.path.rename(new_path)
                    self.load_path(new_path)
                else:
                    self.file.path = new_path

                self.emit('file-changed')

        dialog.connect('response', on_resp)
        dialog.set_transient_for(self.get_root())
        dialog.show()

    def duplicate_file(self):
        assert self.file is not None

        new_path = USER_POOL.new_file_path(self.file.path.stem)

        copy(self.file.path, new_path)

        self.load_path(new_path)
        self.emit('file-changed')

    def load_path(self, path: Path):
        file = DesktopFile(path)
        self.load_file(file)

    def load_file(self, file: DesktopFile):
        self.file = file

        is_pinned = self.file.path.parent == USER_POOL.default_dir
        self.file_menu_button.set_visible(is_pinned)
        self.pin_button.set_visible(not is_pinned)

        self.duplicate_button.set_sensitive(self.file.path.exists())
        self.unpin_button.set_sensitive(self.file.path.exists())

        file_view = FileView()
        file_view.set_file(file)
        self.toolbar_view.set_content(file_view)
        self.window_title.set_title(self.file.get(DesktopEntry.NAME, ''))
        
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

GObject.signal_new('file-leave', FilePage, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
GObject.signal_new('file-changed', FilePage, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
GObject.signal_new('add-string-field', FilePage, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
GObject.signal_new('add-bool-field', FilePage, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
