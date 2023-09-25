from os import access, W_OK
from shutil import copy
from pathlib import Path
from typing import Callable, Optional

from gi.repository import Gtk, Adw, Gio

from .desktop_file import DesktopFile, Field, LocalizedField
from .file_pools import USER_POOL
from .utils import set_icon_from_name, APP_DATA


class BoolRow(Adw.ActionRow):
    __gtype_name__ = 'BoolRow'

    def __init__(self, field: Field[bool]) -> None:
        self.field = field

        self.switch = Gtk.Switch(
            active=field.get(default=False),
            valign=Gtk.Align.CENTER,
        )
        self.switch.connect('state-set', self._on_state_set)

        super().__init__(
            title=field.key,
            activatable_widget=self.switch,
        )
        self.add_suffix(self.switch)

    def _on_state_set(self, widget, value):
        self.field.set(value)

class StringRow(Adw.EntryRow):
    __gtype_name__ = 'StringRow'

    def __init__(self, field: Field[str]) -> None:
        self.field = field

        # TODO: bodge, must implement listrow
        if field._type != str:
            field = Field(field.key, field._parent_section, str)
        
        super().__init__(title=field.key)
        self.set_text(field.get(default=''))
        self.connect('changed', self._on_changed)

    def add_action(self, icon_name: str, callback: Callable):
        button = Gtk.Button(
            valign=Gtk.Align.CENTER,
            icon_name=icon_name,
            css_classes=['flat']
        )
        button.connect('clicked', callback)
        self.add_suffix(button)

    def _on_changed(self, widget):
        self.field.set(self.get_text())

class LocalizedRow(StringRow):
    __gtype_name__='LocaleStringRow'

    def __init__(self, localized_field: LocalizedField[str], locale: str) -> None:
        super().__init__(field = localized_field)

        self.localized_field = localized_field
        self.locale = locale

    def set_locale(self, locale: str):
        self.locale = locale
        self.field = self.localized_field.as_locale(self.locale)

        self.set_title(self.localized_field.key)
        self.set_text(self.localized_field.get_localized(locale, default = ''))

    def _on_changed(self, widget):
        self.localized_field.set_localized(self.locale, self.get_text())

class LocaleChooserRow(Adw.ComboRow):
    __gtype_name__ = 'LocaleChooserRow'

    def __init__(self, locale_list: list[str]) -> None:
        self.locales = locale_list

        model = Gtk.StringList()
        for l in self.locales:
            model.append(l)
        
        super().__init__(
            title = _('Locale'),
            model = model)

        self.add_prefix(Gtk.Image(icon_name='preferences-desktop-locale-symbolic'))

    def connect_localized_rows(self, rows: list[LocalizedRow]):
        def update_rows(*args):
            for row in rows:
                row.set_locale(self.get_current_locale())
        
        self.connect('notify', update_rows)

    def set_default_locale(self):
        self.set_locale(Gtk.get_default_language().to_string())

    def get_current_locale(self) -> str:
        return self.get_selected_item().get_string()

    def set_locale(self, locale: str):
        if locale in self.locales:
            self.set_selected(self.locales.index(locale))


@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/file_page.ui')
class FilePage(Adw.BreakpointBin):
    __gtype_name__ = 'FilePage'

    compact_breakpoint = Gtk.Template.Child('compact_breakpoint')

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

    localized_group = Gtk.Template.Child('localized_group')
    strings_group = Gtk.Template.Child('strings_group')
    bools_group = Gtk.Template.Child('bools_group')

    banner_expanded = True

    @property
    def allow_leave(self) -> bool:
        if self.file is not None:
            return not self.file.edited()
        else:
            return True


    def __init__(self):
        super().__init__()

        self.file: DesktopFile = None

        self.back_button.connect('clicked', lambda _: self.on_leave())
        self.pin_button.connect('clicked', lambda _: self.pin_file())
        self.unpin_button.connect('clicked', lambda _: self.unpin_file())
        self.rename_button.connect('clicked', lambda _: self.rename_file())
        self.duplicate_button.connect('clicked', lambda _: self.duplicate_file())
        self.localized_group.get_header_suffix().connect('clicked', lambda _: self._add_key(is_localized=True))
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
        file_already_exists = self.file.path.exists() # False if file has just been created
        pinned_path = USER_POOL.new_file_name(self.file.path.stem)

        self.file.save_as(pinned_path)
        self.emit('file-changed')

        if not file_already_exists:
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
            if access(self.file.path, W_OK) and self.file.path.exists():
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

        new_path = USER_POOL.new_file_name(self.file.path.stem)

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

        is_pinned = self.file.path.parent == USER_POOL.default_dir
        self.file_menu_button.set_visible(is_pinned)
        self.pin_button.set_visible(not is_pinned)

        self.duplicate_button.set_sensitive(self.file.path.exists())
        self.unpin_button.set_sensitive(self.file.path.exists())

        self.update_page()

    def update_page(self):
        if self.file is None:
            raise ValueError
        
        localized_rows: list[LocalizedRow] = []
        string_rows: list[StringRow] = []
        bool_rows: list[BoolRow] = []

        all_locales = set()
        added_keys = []

        for key, value in self.file.desktop_entry.__dict__().items(): # Adds all non-standard fields
            field = Field.parse_type(key, value, self.file.desktop_entry._section)

            if LocalizedField.split_localized_key(key) is not None:
                unlocalized_key, locale = LocalizedField.split_localized_key(key)

                all_locales |= {locale}

                if unlocalized_key not in added_keys:
                    localized_rows.append(LocalizedRow(LocalizedField(unlocalized_key, field._parent_section, field._type), locale))
                    added_keys.append(unlocalized_key)
            elif key in ['Name', 'Comment']:
                continue
            elif key == 'Icon':
                icon_field = self.file.desktop_entry.Icon

                self.icon_row = StringRow(icon_field)
                self.icon_row.add_action('folder-open-symbolic', lambda _: self._upload_icon())
                self.icon_row.connect('changed', lambda _: self._update_icon())

                string_rows.append(self.icon_row)
            elif field._type in [str, list]:
                string_rows.append(StringRow(field))
            elif field._type == bool:
                bool_rows.append(BoolRow(field))


        if all_locales:
            self.locale_chooser_row = LocaleChooserRow(sorted(list(all_locales)))
            self.locale_chooser_row.connect_localized_rows(localized_rows)
            self.locale_chooser_row.set_default_locale()

            self._update_pref_group(self.localized_group, [self.locale_chooser_row]+localized_rows)
            self.localized_group.set_visible(True)
        else:
            self.localized_group.set_visible(False)

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
            self.window_title.set_title(self.file.desktop_entry.Name.get())
        else:
            self.header_bar.set_show_title(False)

    def _update_icon(self):
        set_icon_from_name(self.app_icon, self.file.desktop_entry.Icon.get())

    def _upload_icon(self):
        def callback(dialog, response):
            if response == Gtk.ResponseType.ACCEPT:
                path = Path(dialog.get_file().get_path())

                # Copy file inside app data directory, so it persists after reboot
                new_path = APP_DATA / 'icons' / path.name

                print(f'{path=}\n{new_path=}')

                copy(path, new_path)

                self.icon_row.field.set(str(new_path))
                self._update_icon()
                self.update_page()

        dialog = Gtk.FileChooserNative(
            title=_('Upload icon'),
            action=Gtk.FileChooserAction.OPEN,
            accept_label=_('Open'),
            cancel_label=_('Cancel'))

        if (path := Path(self.file.desktop_entry.Icon.get(default=''))).exists():
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

        app_name_row = StringRow(self.file.desktop_entry.Name)
        app_name_row.set_margin_bottom(6)
        app_name_row.add_css_class('app-banner-entry')

        app_name_row.connect('changed', lambda _: self._update_window_title())

        if self.banner_expanded:
            app_name_row.set_size_request(0, 64)
            app_name_row.add_css_class('title-1-row')
        else:
            app_name_row.add_css_class('title-2-row')

        app_comment_row = StringRow(self.file.desktop_entry.Comment)
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
            locale = self.locale_chooser_row.get_current_locale()
            locale_entry.set_visible(True)
            locale_entry.set_text(locale)

        key_entry.connect('changed', lambda _: add_key_dialog.set_response_enabled(
            'add', 
            bool(key_entry.get_text())))

        def callback(widget, resp):
            if resp == 'add':
                key = key_entry.get_text()
                value = False if is_bool else ''

                if is_localized: 
                    field = LocalizedField(key, self.file.desktop_entry._section, type(value))
                    field.set_localized(locale_entry.get_text(), value)
                else:
                    field = Field(key, self.file.desktop_entry._section, type(value))
                    field.set(value)

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