from pathlib import Path
from typing import Callable

from gi.repository import Gtk, Adw, Gio

from .desktop_entry import DesktopEntry, Field, LocaleString
from .utils import set_icon_from_name, USER_APPS


class BoolRow(Adw.ActionRow):
    __gtype_name__ = 'BoolRow'

    def __init__(self, field: Field, enabled: bool = True) -> None:
        self.field = field

        self.switch = Gtk.Switch(
            active=field.as_bool(),
            valign=Gtk.Align.CENTER,
            sensitive=enabled,
        )
        self.switch.connect('state-set', self._on_state_set)

        super().__init__(
            title=field.key,
            activatable_widget=self.switch,
            sensitive=enabled,
        )
        self.add_suffix(self.switch)

    def _on_state_set(self, widget, value):
        self.field.set(value)

class StringRow(Adw.EntryRow):
    __gtype_name__ = 'StringRow'

    def __init__(self, field: Field, enabled: bool = True) -> None:
        self.field = field
        
        super().__init__(
            title=field.key,
            sensitive=enabled,
        )
        self.set_text(field.as_str() or '')
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

    def __init__(self, field: Field, locale: 'str | None' = None, enabled: bool = True) -> None:
        super().__init__(
            field=field,
            enabled=enabled,
        )
        self.locale = locale

    def set_locale(self, locale: str):
        self.locale = locale
        self.field = self.field.localize(
            self.locale, 
            return_non_existing_key_as_fallback=True, 
            return_unlocalized_as_fallback=False)

        self.set_title(self.field.unlocalized_key)
        self.set_text(self.field.as_str() or '')

    def _on_changed(self, widget):
        self.field.set(self.get_text())

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

    def connect_localized_rows(self, rows: list[LocalizedRow]):
        def update_rows(*args):
            for row in rows:
                row.set_locale(self.get_current_locale())
        
        self.connect('notify', update_rows)

    def set_current_locale(self):
        self.set_locale(
            str(LocaleString.current().closest(
                [LocaleString.parse(l) for l in self.locales])))

    def get_current_locale(self) -> str:
        return self.get_selected_item().get_string()

    def set_locale(self, locale):
        if locale in self.locales:
            self.set_selected(self.locales.index(locale))


@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/file_page.ui')
class FilePage(Gtk.Box):
    __gtype_name__ = 'FilePage'

    window_title = Gtk.Template.Child('title_widget')
    back_button = Gtk.Template.Child('back_button')
    pin_button = Gtk.Template.Child('pin_button')

    file_menu_button = Gtk.Template.Child('file_menu_button')
    unpin_button = Gtk.Template.Child('unpin_button')

    scrolled_window = Gtk.Template.Child('scrolled_window')

    view_stack = Gtk.Template.Child('view_stack')
    file_view = Gtk.Template.Child('file_view')
    error_view = Gtk.Template.Child('error_view')

    banner_squeezer = Gtk.Template.Child('banner_squeezer')
    banner_box_l = Gtk.Template.Child('banner_box_l')
    
    icon_s = Gtk.Template.Child('icon_s')
    banner_listbox_s = Gtk.Template.Child('banner_listbox_s')
    icon_l = Gtk.Template.Child('icon_l')
    banner_listbox_l = Gtk.Template.Child('banner_listbox_l')

    @property
    def banner_expanded(self) -> bool:
        return self.banner_squeezer.get_visible_child() == self.banner_box_l
    
    @property
    def app_icon(self):
        return self.icon_l if self.banner_expanded else self.icon_s
    @app_icon.setter
    def app_icon(self, value: Gtk.Image):
        if self.banner_expanded:
            self.icon_l = value
        else:
            self.icon_s = value

    @property
    def banner_listbox(self):
        return self.banner_listbox_l if self.banner_expanded else self.banner_listbox_s
    
    localized_group = Gtk.Template.Child('localized_group')
    strings_group = Gtk.Template.Child('strings_group')
    bools_group = Gtk.Template.Child('bools_group')


    def __init__(self):
        super().__init__()

        self.file = None

        self.banner_squeezer.connect('notify', lambda *_: self._update_app_banner())
        self.back_button.connect('clicked', lambda _: self.on_leave())
        self.unpin_button.connect('clicked', lambda _: self.unpin_file())
        self.pin_button.connect('clicked', lambda _: self.pin_file())
        self.localized_group.get_header_suffix().connect('clicked', lambda _: self._add_key(is_localized=True))
        self.strings_group.get_header_suffix().connect('clicked', lambda _: self._add_key())
        self.bools_group.get_header_suffix().connect('clicked', lambda _: self._add_key(is_bool=True))

    def pin_file(self):
        '''Saves a file to the user folder. Used when the file does not exist or it does not have write access.'''
        assert self.file is not None

        if not self.visible:
            return

        pinned_path: Path = USER_APPS / self.file.filename

        self.file.save(pinned_path)
        self.emit('file-changed')
        self.load_path(pinned_path)

    def on_leave(self):
        '''Called when the page is about to be closed, e.g. when `Escape` is pressed or when the app is closed'''
        assert self.file is not None

        if not self.file.path.exists():
            return

        if self.file.edited():
            if self.file.write_permission:
                self.file.save()
                self.emit('file-changed')
                self.emit('file-leave')
            else:
                builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/file_page_dialogs.ui')

                dialog = builder.get_object('save_changes_dialog')

                def callback(widget, resp):
                    if resp == 'discard':
                        self.emit('file-leave')
                    elif resp == 'pin':
                        self.pin_file()

                dialog.connect('response', callback)
                dialog.set_transient_for(self.get_root())
                dialog.present()
        else:
            self.emit('file-leave')

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

    def load_path(self, path: Path):
        try:
            file = DesktopEntry(path)
        except (FileExistsError, PermissionError):
            self.view_stack.set_visible_child(self.error_view)
        else:
            self.load_file(file)

    def load_file(self, file: DesktopEntry):
        self.view_stack.set_visible_child(self.file_view)
        self.file = file

        self.scrolled_window.set_vadjustment(Gtk.Adjustment.new(0, 0, 0, 0, 0, 0))

        is_pinned = self.file.path.parent == USER_APPS
        self.file_menu_button.set_visible(is_pinned)
        self.pin_button.set_visible(not is_pinned)

        self.update_page()

    def update_page(self):
        if self.file is None:
            raise ValueError
        
        localized_rows: list[LocalizedRow] = []
        string_rows: list[StringRow] = []
        bool_rows: list[BoolRow] = []

        all_locales = set()
        added_keys = []

        rows_enabled = self.file.write_permission

        for key, field in self.file.appsection.items():
            if field.locale is not None:
                all_locales = all_locales | {f.locale for f in field.localized_fields if f.locale is not None}

                if field.unlocalized_key not in added_keys:
                    localized_rows.append(LocalizedRow(field, enabled=rows_enabled))
                    added_keys.append(field.unlocalized_key)
            elif key in ['Name', 'Comment']:
                continue
            elif key == 'Icon':
                icon_field = self.file.appsection.Icon

                self.icon_row = StringRow(icon_field, enabled=rows_enabled)
                self.icon_row.add_action('folder-open-symbolic', lambda _: self._upload_icon())
                self.icon_row.connect('changed', lambda _: self._update_icon())

                string_rows.append(self.icon_row)
            elif type(field.get()) in [str, list]:
                string_rows.append(StringRow(field, enabled=rows_enabled))
            elif type(field.get()) == bool:
                bool_rows.append(BoolRow(field, enabled=rows_enabled))


        if all_locales:
            self.locale_chooser_row = LocaleChooserRow(sorted(list(all_locales)))
            self.locale_chooser_row.connect_localized_rows(localized_rows)
            self.locale_chooser_row.set_current_locale()

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

        self._update_app_banner()

    @property
    def visible(self):
        return isinstance(self.get_parent().get_visible_child(), FilePage)

    def _update_icon(self):
        set_icon_from_name(self.app_icon, self.icon_row.field.as_str())

    def _upload_icon(self):
        def callback(dialog, response):
            if response == Gtk.ResponseType.ACCEPT:
                path = dialog.get_file().get_path()
                self.icon_row.field.set(path)
                self._update_icon()
                self.update_page()

        dialog = Gtk.FileChooserNative(
            title=_('Upload icon'),
            action=Gtk.FileChooserAction.OPEN,
            accept_label=_('Open'),
            cancel_label=_('Cancel'))

        if (path := Path(self.file.appsection.Icon.as_str())).exists():
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

        app_name_row = StringRow(self.file.appsection.Name)
        app_name_row.set_margin_bottom(6)
        app_name_row.add_css_class('app-banner-entry')

        if self.banner_expanded:
            app_name_row.set_size_request(0, 64)
            app_name_row.add_css_class('title-1-row')
        else:
            app_name_row.add_css_class('title-2-row')

        app_comment_row = StringRow(self.file.appsection.Comment)
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

                field = Field(key, self.file.appsection.section)
                if is_localized and (locale := locale_entry.get_text()): 
                    field = field.localize(
                        locale,
                        return_non_existing_key_as_fallback=True,
                        return_unlocalized_as_fallback=False)
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