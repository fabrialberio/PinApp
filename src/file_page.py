from shutil import copy
from pathlib import Path
from typing import Callable, Optional, get_origin

from gi.repository import Gtk, Adw, Gio, GObject # type: ignore
from gettext import gettext as _

from .desktop_file import DesktopFile, DesktopEntry, Field, LocaleField
from .config import set_icon_from_name, new_file_name, USER_APPS, APP_DATA


class BoolRow(Adw.ActionRow):
    __gtype_name__ = 'BoolRow'

    def __init__(self, file: DesktopFile, field: Field[bool]) -> None:
        switch = Gtk.Switch(
            active=file.get(field, False),
            valign=Gtk.Align.CENTER,
        )
        switch.set_active(file[field])

        super().__init__(
            title=field.key,
            activatable_widget=switch,
        )
        self.add_suffix(switch)

        def on_state_set(self, widget: Gtk.Switch, value: bool):
            file.set(field, value)

        def on_field_set(file: DesktopFile, field_: Field[bool], value: bool):
            if field_ == field and value != self.get_active():
                switch.set_active(value)

        switch.connect('state-set', on_state_set)
        file.connect('field-set', on_field_set)

class StringRow(Adw.EntryRow):
    __gtype_name__ = 'StringRow'

    def __init__(self, file: DesktopFile, field: Field[str]) -> None:
        super().__init__(title=field.key)
        self.set_text(file.get(field, ''))

        def on_changed(widget: StringRow):
            file.set(field, self.get_text())
        
        def on_field_set(file: DesktopFile, field_: Field[str], value: str):
            if field_ == field and value != self.get_text():
                self.set_text(value)

        self.connect('changed', on_changed)
        file.connect('field-set', on_field_set)

    def add_action(self, icon_name: str, callback: Callable[[Gtk.Widget], None]):
        button = Gtk.Button(
            valign=Gtk.Align.CENTER,
            icon_name=icon_name,
            css_classes=['flat']
        )
        button.connect('clicked', callback)
        self.add_suffix(button)

class LocaleStringRow(Adw.EntryRow):
    __gtype_name__ = 'LocaleStringRow'

    file: DesktopFile
    field: LocaleField[str]
    locale: str

    def __init__(self, file: DesktopFile, field: LocaleField[str], locale: str) -> None:
        super().__init__(title=field.key)

        self.file = file
        self.field = field
        self.locale = locale

        self.set_locale(locale)

        def on_changed(widget: StringRow):
            self.file.set(self.field.localize(self.locale), self.get_text())
        
        def on_field_set(file: DesktopFile, field_: Field[str], value: str):
            if field_ == field.localize(locale) and value != self.get_text():
                self.set_text(value)

        self.connect('changed', on_changed)
        file.connect('field-set', on_field_set)

    def set_locale(self, locale: str):
        self.locale = locale
        self.set_text(self.file.get(self.field.localize(self.locale), ''))

class LocaleStringsGroup(Adw.PreferencesGroup):
    __gtype_name__ = 'LocaleStringsGroup'

    def __init__(self) -> None:
        super().__init__(title=_('Localized values'))

    def set_fields(self, file: DesktopFile, fields: list[LocaleField]):        
        self.get_first_child().get_last_child().get_first_child().remove_all()
        
        locales = sorted(list(set([l for f in fields for l in file.locales(f)])))
        
        locale_chooser_row = Adw.ComboRow(
            title=_('Locale'),
            model=Gtk.StringList.new(locales)
        )
        locale_chooser_row.add_prefix(Gtk.Image(icon_name='preferences-desktop-locale-symbolic'))

        rows = [LocaleStringRow(file, f, locale_chooser_row.get_selected_item()) for f in fields]

        self.add(locale_chooser_row)
        for row in rows:
            self.add(row)

        def update_rows(widget: LocaleStringsGroup, pspec, user_data):
            for row in rows:
                row.set_locale(locale_chooser_row.get_selected_item())

        self.connect('notify', update_rows)


@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/file_page.ui')
class FilePage(Adw.BreakpointBin):
    __gtype_name__ = 'FilePage'

    compact_breakpoint = Gtk.Template.Child()

    window_title = Gtk.Template.Child('window_title')
    header_bar = Gtk.Template.Child('header_bar')
    back_button = Gtk.Template.Child('back_button')
    pin_button = Gtk.Template.Child('pin_button')

    file_menu_button = Gtk.Template.Child('file_menu_button')
    unpin_button = Gtk.Template.Child('unpin_button')
    rename_button = Gtk.Template.Child('rename_button')
    duplicate_button = Gtk.Template.Child('duplicate_button')

    scrolled_window = Gtk.Template.Child('scrolled_window')

    view_stack = Gtk.Template.Child('view_stack')
    file_view = Gtk.Template.Child('file_view')
    error_view = Gtk.Template.Child('error_view')

    app_icon = Gtk.Template.Child('icon')
    banner_listbox = Gtk.Template.Child('banner_listbox')

    locale_strings_group = Gtk.Template.Child('locale_strings_group')
    strings_group = Gtk.Template.Child('strings_group')
    bools_group = Gtk.Template.Child('bools_group')

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

        self.back_button.connect('clicked', lambda _: self.on_leave())
        self.pin_button.connect('clicked', lambda _: self.pin_file())
        self.unpin_button.connect('clicked', lambda _: self.unpin_file())
        self.rename_button.connect('clicked', lambda _: self.rename_file())
        self.duplicate_button.connect('clicked', lambda _: self.duplicate_file())
        #self.localized_group.get_header_suffix().connect('clicked', lambda _: self._add_key(is_localized=True))
        self.strings_group.get_header_suffix().connect('clicked', lambda _: self._add_key())
        self.bools_group.get_header_suffix().connect('clicked', lambda _: self._add_key(is_bool=True))

        def _set_banner_expanded(value: bool):
            self.banner_expanded = value
            self._update_app_banner()

        self.compact_breakpoint.connect('apply', lambda _: _set_banner_expanded(False))
        self.compact_breakpoint.connect('unapply', lambda _: _set_banner_expanded(True))
        self.scrolled_window.get_vadjustment().connect('value-changed', lambda _: self._update_window_title())

    def pin_file(self):
        '''Saves a file to the user folder. Used when the file does not exist or it does not have write access.'''
        assert self.file is not None

        is_new_file = not self.file.path.exists()
        pinned_path: Path = new_file_name(USER_APPS, self.file.path.stem)

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
                self.file.delete()
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
            return USER_APPS / Path(f'{Path(name_entry.get_text())}.desktop')


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

        new_path = new_file_name(USER_APPS, self.file.path.stem)

        copy(self.file.path, new_path)

        self.load_path(new_path)
        self.emit('file-changed')

    def load_path(self, path: Path):
        try:
            file = DesktopFile(path)
        except (FileExistsError, PermissionError):
            self.view_stack.set_visible_child(self.error_view)
        else:
            self.load_file(file)

    def load_file(self, file: DesktopFile):
        self.view_stack.set_visible_child(self.file_view)
        self.file = file

        self.scrolled_window.get_vadjustment().set_value(0)

        is_pinned = self.file.path.parent == USER_APPS
        self.file_menu_button.set_visible(is_pinned)
        self.pin_button.set_visible(not is_pinned)

        self.duplicate_button.set_sensitive(self.file.path.exists())
        self.unpin_button.set_sensitive(self.file.path.exists())

        self.update_page()

    def update_page(self):
        if self.file is None:
            raise ValueError

        string_rows: list[StringRow] = []
        bool_rows: list[BoolRow] = []

        locale_fields = []

        for field in self.file.fields(DesktopEntry.group):
            if field.key in [f.key for f in DesktopEntry.fields]:
                field = next(f for f in DesktopEntry.fields if f.key == field.key)

            if isinstance(field, LocaleField):
                locale_fields.append(field)
            elif field == DesktopEntry.NAME or field == DesktopEntry.COMMENT:
                continue
            elif field == DesktopEntry.ICON:
                icon_row = StringRow(self.file, DesktopEntry.ICON)
                icon_row.add_action('folder-open-symbolic', lambda _: self._upload_icon())
                icon_row.connect('changed', lambda _: self._update_icon())

                string_rows.append(icon_row)
            elif field._type == str:
                string_rows.append(StringRow(self.file, field)) # type: ignore
            elif field._type == bool:
                bool_rows.append(BoolRow(self.file, field)) # type: ignore
            elif get_origin(field._type) == list:
                string_rows.append(StringRow(self.file, Field(field.group, field.key, str)))

        if locale_fields:
            self.locale_strings_group.set_fields(self.file, locale_fields)
            self.locale_strings_group.set_visible(True)
        else:
            self.locale_strings_group.set_visible(False)

        self._update_pref_group(
            pref_group=self.strings_group,
            new_children=string_rows, 
            empty_message=_('No string values present'))

        self._update_pref_group(
            pref_group=self.bools_group, 
            new_children=bool_rows, 
            empty_message=_('No boolean values present'))

        self._update_window_title()
        self._update_app_banner()

    def _update_window_title(self):
        if self.scrolled_window.get_vadjustment().get_value() > 0:
            self.header_bar.set_show_title(True)
            self.window_title.set_title(self.file.get(DesktopEntry.NAME, ''))
        else:
            self.header_bar.set_show_title(False)

    def _update_icon(self):
        set_icon_from_name(self.app_icon, self.file.get(DesktopEntry.ICON, ''))

    def _upload_icon(self):
        def callback(dialog, response):
            if response == Gtk.ResponseType.ACCEPT:
                path = Path(dialog.get_file().get_path())

                # Copy file inside app data directory, so it persists after reboot
                new_path = APP_DATA / 'icons' / path.name

                print(f'{path=}\n{new_path=}')

                copy(path, new_path)

                self.file.set(DesktopEntry.ICON, str(new_path))
                self._update_icon()
                self.update_page()

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

    def _update_app_banner(self):
        if self.file is None:
            return

        while (row := self.banner_listbox.get_row_at_index(0)) != None:
            self.banner_listbox.remove(row)

        app_name_row = StringRow(self.file, DesktopEntry.NAME)
        app_name_row.set_margin_bottom(6)
        app_name_row.add_css_class('app-banner-entry')

        app_name_row.connect('changed', lambda _: self._update_window_title())

        if self.banner_expanded:
            app_name_row.set_size_request(0, 64)
            app_name_row.add_css_class('title-1-row')
        else:
            app_name_row.add_css_class('title-2-row')

        app_comment_row = StringRow(self.file, DesktopEntry.COMMENT)
        app_comment_row.add_css_class('app-banner-entry')

        self.banner_listbox.append(app_name_row)
        self.banner_listbox.append(app_comment_row)
        self._update_icon()

    def _add_key(self, is_bool=False, is_localized=False):
        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/file_page_dialogs.ui')

        add_key_dialog = builder.get_object('add_key_dialog')
        locale_entry = builder.get_object('locale_entry')
        key_entry = builder.get_object('key_entry')

        if is_localized:
            locale = self.locale_chooser_row.get_locale()
            locale_entry.set_visible(True)
            locale_entry.set_text(locale)

        key_entry.connect('changed', lambda _: add_key_dialog.set_response_enabled(
            'add', 
            bool(key_entry.get_text())))

        def callback(widget, resp):
            if resp == 'add':
                group = DesktopEntry.group
                key = key_entry.get_text()
                
                if is_bool:
                    self.file.set(Field(group, key, bool), False)
                else:
                    if is_localized:
                        self.file.set(LocaleField(group, key, str).localize(locale_entry.get_text()))
                    else:
                        self.file.set(Field(group, key, str), '')

                self.update_page()

        add_key_dialog.connect('response', callback)
        add_key_dialog.set_transient_for(self.get_root())
        add_key_dialog.present()

    def _update_pref_group(self, pref_group: Adw.PreferencesGroup, new_children: list[Gtk.Widget], empty_message: 'str | None'=None):
        '''Removes all present children of the group and adds the new ones'''

        listbox = (
            pref_group
            .get_first_child()  # Main group GtkBox
            .get_last_child()   # GtkBox containing the listbox
            .get_first_child()) # GtkListbox

        if listbox != None:
            while (row := listbox.get_first_child()) != None:
                pref_group.remove(row)

        if len(new_children) > 0:
            for c in new_children:
                pref_group.add(c)
        elif empty_message != None:
            pref_group.add(Adw.ActionRow(
                title=empty_message,
                title_lines=1,
                css_classes=['dim-label'],
                halign=Gtk.Align.CENTER,
            ))

GObject.signal_new('file-leave', FilePage, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
GObject.signal_new('file-changed', FilePage, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
GObject.signal_new('add-string-field', FilePage, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
GObject.signal_new('add-bool-field', FilePage, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
