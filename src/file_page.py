from gi.repository import Gtk, Gio, Adw, GObject

from pathlib import Path
from os import access, W_OK

from .folders import DesktopEntryFolder
from .desktop_entry import DesktopEntry, Field

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

    app_icon = Gtk.Template.Child('app_icon')
    banner_box = Gtk.Template.Child('name_comment_listbox')

    locale_combo_row = Gtk.Template.Child('locale_combo_row')
    localized_group = Gtk.Template.Child('localized_group')
    strings_group = Gtk.Template.Child('strings_group')
    bools_group = Gtk.Template.Child('bools_group')


    def __init__(self):
        super().__init__()

        self.file = None

        self.back_button.connect('clicked', lambda _: self.emit('file-back'))
        self.back_button.connect('clicked', lambda _: self.emit('file-back'))
        self.unpin_button.connect('clicked', lambda _: self.delete_file())
        self.save_button.connect('clicked', lambda _: self.save_file())
        self.pin_button.connect('clicked', lambda _: self.pin_file())
        self.strings_group.get_header_suffix().connect('clicked', lambda _: self._add_key())
        self.bools_group.get_header_suffix().connect('clicked', lambda _: self._add_key(is_bool=True))

        model = Gtk.StringList()
        for i in range(10):
            model.append(str(i))

        self.locale_combo_row.set_model(model)

    @property
    def visible(self):
        return isinstance(self.get_parent().get_visible_child(), FilePage)

    def delete_file(self):
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
        
        if self.file.path.exists():
            self.file.load()

        self.scrolled_window.set_vadjustment(Gtk.Adjustment.new(0, 0, 0, 0, 0, 0))

        while (row := self.banner_box.get_row_at_index(0)) != None:
            self.banner_box.remove(row)

        app_name_row = StringRow(self.file.appsection.Name)
        # Style the text
        (app_name_row
            .get_first_child() # GtkBox containing the header
            .observe_children() # List of all children
            .get_item(1) # Get second child (editable area)
            .get_last_child() # GtkText
            .add_css_class('title-1'))
        app_name_row.set_margin_bottom(4)
        app_name_row.set_size_request(64, 64)
        app_comment_row = StringRow(self.file.appsection.Comment)
        
        self.banner_box.append(app_name_row)
        self.banner_box.append(app_comment_row)

        self.window_title.set_subtitle(self.file.filename)

        writable = self.file.writable
        self.save_button.set_visible(writable)
        self.unpin_button.set_visible(writable)
        self.pin_button.set_visible(not writable)

        self.update_file()

    def update_file(self):
        file_dict: dict = self.file.appsection.as_dict()

        self._update_icon()

        file_dict.pop('Name', '')
        file_dict.pop('Comment', '')

        localized_rows = LocaleStringRow.list_from_field_list(list(self.file.appsection.values()))
        self._update_pref_group(self.localized_group, localized_rows)

        if (icon_field := file_dict.get('Icon', None)) != None:
            file_dict.pop('Icon', '')
            icon_row = StringRow(icon_field)
            icon_row.connect('changed', lambda _: self._update_icon())
            string_rows = [icon_row]
        else:
            string_rows = []
        string_rows += StringRow.list_from_field_list(file_dict.values())
        self._update_pref_group(self.strings_group, string_rows, Adw.ActionRow(
            title=_('No string values present'),
            title_lines=1,
            css_classes=['dim-label'],
            halign=Gtk.Align.CENTER))

        bool_rows = BoolRow.list_from_field_list(file_dict.values())
        self._update_pref_group(self.bools_group, bool_rows, Adw.ActionRow(
            title=_('No boolean values present'),
            title_lines=1,
            css_classes=['dim-label'],
            halign=Gtk.Align.CENTER))

        if localized_rows:
            self.localized_group.set_visible(True)
        else:
            self.localized_group.set_visible(False)

    def _update_icon(self):
        icon_name = self.file.appsection.Icon.get()
        if icon_name == None:
            self.app_icon.set_from_icon_name('image-missing')
        elif Path(icon_name).exists():
            self.app_icon.set_from_file(icon_name)
        else:
            self.app_icon.set_from_icon_name(icon_name)

    def save_file(self):
        if not self.visible: 
            return

        self.file.save()
        self.emit('file-save')

    def pin_file(self):
        if not self.visible:
            return

        self.file.save(Path(DesktopEntryFolder.USER)/self.file.filename)
        self.emit('file-save')

    def _add_key(self, is_bool=False):
        builder = Gtk.Builder.new_from_resource('/io/github/fabrialberio/pinapp/file_page_dialogs.ui')

        add_key_dialog = builder.get_object('add_key_dialog')
        key_entry = builder.get_object('key_entry')

        key_entry.connect('changed', lambda _: add_key_dialog.set_response_enabled(
            'add', 
            bool(key_entry.get_text())))

        def callback(widget, resp):
            if resp == 'add':
                self.file.appsection.add_entry(key_entry.get_text(), False if is_bool else '')
                self.update_file()

        add_key_dialog.connect('response', callback)
        add_key_dialog.set_transient_for(self.get_root())
        add_key_dialog.present()


    def _update_pref_group(self, pref_group: Adw.PreferencesGroup, new_children: list[Gtk.Widget], empty_state: Gtk.Widget = None):
        '''Removes all present children of the group and adds the new ones'''

        listbox = (
            pref_group
            .get_first_child()  # Main group GtkBox
            .get_last_child()   # GtkBox containing the listbox
            .get_first_child()) # GtkListbox

        while (row := listbox.get_first_child()) != None:
            pref_group.remove(row)

        if len(new_children) > 0:
            for c in new_children:
                pref_group.add(c)
        elif empty_state != None:
            pref_group.add(empty_state)


class BoolRow(Adw.ActionRow):
    def __init__(self, field: Field) -> None:
        self.field = field

        self.switch = Gtk.Switch(
            active=field.as_bool(),
            valign=Gtk.Align.CENTER,
        )
        self.switch.connect('state-set', self.on_state_set)

        super().__init__(
            title=field.key,
            activatable_widget=self.switch,
        )
        self.add_suffix(self.switch)

    @staticmethod
    def list_from_field_list(fields: list[Field]):
        return [BoolRow(f) for f in fields if type(f.get()) == bool]

    def on_state_set(self, widget, value):
        self.field.set(value)

class StringRow(Adw.EntryRow):
    def __init__(self, field: Field) -> None:
        self.field = field
        
        super().__init__(title=field.key)
        self.set_text(field.as_str() or '')
        self.connect('changed', self.on_changed)
        
    def add_action(self, icon_name: str, tooltip: str, callback):
        button = Gtk.Button(
                icon_name=icon_name,
                tooltip_text=tooltip,
                valign=Gtk.Align.CENTER,
                css_classes=['flat'])

        button.connect('clicked', callback)
        self.add_suffix(button)


    @staticmethod
    def list_from_field_list(fields: list[Field]):
        return [StringRow(f) for f in fields if ((t := type(f.get())) == str or t == list) and not f.locale]

    def on_changed(self, widget):
        self.field.set(self.get_text())

class LocaleStringRow(Adw.EntryRow):
    def __init__(self, field: Field) -> None:
        self.field = field

        locales = [f.locale for f in self.field.localized_fields]
        self.dropdown = Gtk.DropDown.new_from_strings(sorted(locales))
        self.dropdown.set_valign(Gtk.Align.CENTER)
        self.dropdown.connect('notify', self._on_dropdown_notify)

        super().__init__(title=field.key.capitalize())
        self.add_suffix(self.dropdown)
        self.connect('changed', self._on_changed)

    @staticmethod
    def list_from_field_list(fields: list[Field]):
        if len(fields) > 0:
            # Assumes that all keys are in the same section
            section = fields[0].section
            
            # All keys that have a locale, but stripped of it
            localized_keys = [f.unlocalized_key for f in fields if f.localized_fields]
            # Remove duplicates
            localized_keys = list(dict.fromkeys(localized_keys))

            return [LocaleStringRow(Field(k, section)) for k in localized_keys]
        else:
            return []

    @property
    def selected_locale(self):
        return self.dropdown.get_selected_item().get_string()

    def _on_dropdown_notify(self, widget, value):
        self.set_text(self.field.localize(self.selected_locale).as_str())

    def _on_changed(self, widget):
        self.field.localize(self.selected_locale).set(self.get_text())