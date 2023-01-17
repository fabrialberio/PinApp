from pathlib import Path
from typing import Callable

from gi.repository import Gtk, Adw, Gio

from .desktop_entry import DesktopEntry, Field, LocaleString
from .utils import set_icon_from_name, USER_APPS


class BoolRow(Adw.ActionRow):
    @staticmethod
    def list_from_field_list(fields: list[Field]):
        return [BoolRow(f) for f in fields if type(f.get()) == bool]

    def __init__(self, field: Field) -> None:
        self.field = field

        self.switch = Gtk.Switch(
            active=field.as_bool(),
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
    __gtype_name__='StringRow'

    @staticmethod
    def list_from_field_list(fields: list[Field]):
        return [StringRow(f) for f in fields if ((t := type(f.get())) == str or t == list) and not f.locale]

    def __init__(self, field: Field) -> None:
        self.field = field
        
        super().__init__(title=field.key)
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

    def __init__(self, field: Field, locale: 'str | None' = None) -> None:
        super().__init__(field=field)
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

    def set_locale(self, locale):
        if locale in self.locales:
            self.set_selected(self.locales.index(locale))


@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/file_page.ui')
class FilePage(Gtk.Box):
    __gtype_name__ = 'FilePage'

    window_title = Gtk.Template.Child('title_widget')
    back_button = Gtk.Template.Child('back_button')
    unpin_button = Gtk.Template.Child('unpin_button')
    save_button = Gtk.Template.Child('save_button')
    pin_button = Gtk.Template.Child('pin_button')

    scrolled_window = Gtk.Template.Child('scrolled_window')
    main_view = Gtk.Template.Child('main_box')

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
        self.back_button.connect('clicked', lambda _: self.emit('file-back'))
        self.back_button.connect('clicked', lambda _: self.emit('file-back'))
        self.unpin_button.connect('clicked', lambda _: self.delete_file())
        self.save_button.connect('clicked', lambda _: self.save_file())
        self.pin_button.connect('clicked', lambda _: self.pin_file())
        self.localized_group.get_header_suffix().connect('clicked', lambda _: self._add_key(is_localized=True))
        self.strings_group.get_header_suffix().connect('clicked', lambda _: self._add_key())
        self.bools_group.get_header_suffix().connect('clicked', lambda _: self._add_key(is_bool=True))

    def save_file(self):
        '''Saves a file to its current folder.'''
        if not self.visible: 
            return

        if not self.file.writable:
            self.pin_file()
            return

        # Removes all empty localized fields (to clean up the file)
        self.file.filter_items(lambda k, v: False if '[' in k and not v else True)

        self.file.save()
        self.emit('file-save')

    def pin_file(self):
        '''Saves a file to the user folder. Used when the file does not exist or it does not have write access.'''
        if not self.visible:
            return

        self.file.save(USER_APPS / self.file.filename)
        self.emit('file-save')

    def delete_file(self):
        '''Deletes a file. It is used when the file has write access.'''
        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/file_page_dialogs.ui')
        
        dialog = builder.get_object('confirm_delete_dialog')

        def callback(widget, resp):
            if resp == 'delete':
                self.file.delete()
                self.emit('file-delete')

        dialog.connect('response', callback)
        dialog.set_transient_for(self.get_root())
        dialog.present()

    def load_file(self, file: DesktopEntry):
        self.file = file

        self._update_app_banner()

        self.scrolled_window.set_vadjustment(Gtk.Adjustment.new(0, 0, 0, 0, 0, 0))

        self.save_button.set_visible(self.file.writable)
        self.unpin_button.set_visible(self.file.path.parent == USER_APPS and self.file.path.exists())
        self.pin_button.set_visible(self.file.path.parent != USER_APPS or not self.file.path.exists())

        self.update_file()

    def update_file(self):
        file_dict: dict = self.file.appsection.as_dict()
        file_dict.pop('Name', '')
        file_dict.pop('Comment', '')
        file_dict.pop('Icon', '')

        self._update_locale()
        icon_row = self._get_icon_row()

        string_rows = [icon_row] + StringRow.list_from_field_list(file_dict.values())
        self._update_pref_group(
            pref_group=self.strings_group,
            new_children=string_rows, 
            empty_message=_('No string values present'))

        bool_rows = BoolRow.list_from_field_list(file_dict.values())
        self._update_pref_group(
            pref_group=self.bools_group, 
            new_children=bool_rows, 
            empty_message=_('No boolean values present'))

    @property
    def visible(self):
        return isinstance(self.get_parent().get_visible_child(), FilePage)

    def _get_icon_row(self, value: str=None) -> StringRow:
        icon_field = self.file.appsection.Icon
        if value != None:
            icon_field.set(value)
        
        icon_row = StringRow(icon_field)
        icon_row.add_action('folder-open-symbolic', lambda _: self._upload_icon())
        icon_row.connect('changed', lambda _: self._get_icon_row())

        self.app_icon = set_icon_from_name(self.app_icon, icon_field.as_str())

        return icon_row

    def _upload_icon(self):
        def callback(dialog, response):
            if response == Gtk.ResponseType.ACCEPT:
                path = dialog.get_file().get_path()
                self._get_icon_row(path)
                self.update_file()

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
        if self.file == None:
            return

        while (row := self.banner_listbox.get_row_at_index(0)) != None:
            self.banner_listbox.remove(row)

        app_name_row = StringRow(self.file.appsection.Name)
        # Style app name
        app_name_text = (app_name_row
            .get_first_child() # GtkBox containing the header
            .observe_children() # List of all children
            .get_item(1) # Get second child (editable area)
            .get_last_child()) # GtkText
        app_name_row.set_margin_bottom(6)
        app_name_row.add_css_class('app-banner-entry')

        if self.banner_expanded:
            app_name_row.set_size_request(0, 64)
            app_name_text.add_css_class('title-1')
        else:
            app_name_text.add_css_class('title-2')

        app_comment_row = StringRow(self.file.appsection.Comment)
        app_comment_row.add_css_class('app-banner-entry')

        self.banner_listbox.append(app_name_row)
        self.banner_listbox.append(app_comment_row)
        self._get_icon_row()

    def _update_locale(self):
        all_locales = set()
        localized_rows: list[LocalizedRow] = []
        added_keys = [] # This list is used to avoid duplicates in a performance-efficient way
        for field in self.file.appsection.values():
            if field.locale:
                all_locales = all_locales | {f.locale for f in field.localized_fields}
                if (k := field.unlocalized_key) not in added_keys:
                    localized_rows.append(LocalizedRow(field))
                    added_keys.append(k)

        all_locales = list(all_locales)
        self.locale_chooser_row = LocaleChooserRow(sorted(all_locales))
        
        if all_locales:
            def update_row_locales(*args):
                for row in localized_rows:
                    row.set_locale(self.locale_chooser_row.get_selected_item().get_string())

            self.locale_chooser_row.connect('notify', update_row_locales)
            self.locale_chooser_row.set_locale(
                str(LocaleString.current().closest(
                    [LocaleString.parse(l) for l in all_locales])))

            self._update_pref_group(self.localized_group, [self.locale_chooser_row] + localized_rows)
            self.localized_group.set_visible(True)
        else:
            self.localized_group.set_visible(False)

    def _add_key(self, is_bool=False, is_localized=False):
        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/file_page_dialogs.ui')

        add_key_dialog = builder.get_object('add_key_dialog')
        locale_entry = builder.get_object('locale_entry')
        key_entry = builder.get_object('key_entry')

        if is_localized:
            locale = self.locale_chooser_row.get_selected_item().get_string()
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

                self.update_file()

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