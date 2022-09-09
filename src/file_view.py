from gi.repository import Gtk, Gio, Adw, GObject

from .desktop_entry import DesktopFile, Field

@Gtk.Template(resource_path='/com/github/fabrialberio/pinapp/file_view.ui')
class FileView(Gtk.Box):
    __gtype_name__ = 'FileView'

    window_title = Gtk.Template.Child('title_widget')
    back_button = Gtk.Template.Child('back_button')
    save_button = Gtk.Template.Child('save_button')
    delete_button = Gtk.Template.Child('delete_button')
    main_view = Gtk.Template.Child('main_box')

    app_icon = Gtk.Template.Child('app_icon')
    banner_box = Gtk.Template.Child('name_comment_box')
    
    localized_group = Gtk.Template.Child('localized_group')
    strings_group = Gtk.Template.Child('strings_group')
    bools_group = Gtk.Template.Child('bools_group')

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.file = None

        GObject.type_register(FileView)
        GObject.signal_new('file-back', FileView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
        GObject.signal_new('file-save', FileView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
        GObject.signal_new('file-delete', FileView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
        GObject.signal_new('file-edit', FileView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
        GObject.signal_new('add-string-field', FileView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
        GObject.signal_new('add-bool-field', FileView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())

        self.back_button.connect('clicked', lambda _: self.emit('file-back'))
        self.save_button.connect('clicked', lambda _: self.emit('file-save'))
        self.delete_button.connect('clicked', lambda _: self.emit('file-delete'))
        self.strings_group.get_header_suffix().connect('clicked', lambda _: self._show_add_key_dialog())
        self.bools_group.get_header_suffix().connect('clicked', lambda _: self._show_add_key_dialog(is_bool=True))

    def load_file(self, file: DesktopFile, is_new = False):
        self.file = file
        self.file.load()

        while self.banner_box.get_first_child():
            self.banner_box.remove(self.banner_box.get_first_child())

        app_name_row = StringRow(self.file.appsection.Name)
        app_name_row.add_css_class('title-2')
        app_comment_row = StringRow(self.file.appsection.Comment)
        
        self.banner_box.append(app_name_row)
        self.banner_box.append(app_comment_row)

        self.window_title.set_subtitle(self.file.filename)
        self.save_button.set_sensitive(True)

        if is_new:
            self.delete_button.set_visible(False)
        else:
            self.delete_button.set_visible(True)

        self.build_ui()

    def build_ui(self):
        file_dict: dict = self.file.appsection.as_dict()

        self.app_icon.set_from_icon_name(self.file.appsection.Icon.get() or 'image-missing')
        file_dict.pop('Name', '')
        file_dict.pop('Comment', '')

        localized_rows = LocaleStringRow.list_from_field_list(self.file.appsection.values())
        self._update_preferences_group(self.localized_group, localized_rows)

        string_rows = StringRow.list_from_field_list(file_dict.values())
        self._update_preferences_group(self.strings_group, string_rows)

        bool_rows = BoolRow.list_from_field_list(file_dict.values())
        self._update_preferences_group(self.bools_group, bool_rows)

        if localized_rows:
            self.localized_group.set_visible(True)
        else:
            self.localized_group.set_visible(False)


    def _show_add_key_dialog(self, is_bool=False):
        add_key_dialog = Adw.MessageDialog(
            width_request=400,
            heading=_('Add new key'),
            default_response='add',
            close_response='cancel')
        add_key_dialog.add_response('cancel', _('Cancel'))
        add_key_dialog.add_response('add', _('Add'))
        add_key_dialog.set_response_enabled('add', False)
        add_key_dialog.set_response_appearance('add', Adw.ResponseAppearance.SUGGESTED)

        key_row = Adw.EntryRow(title=_('Key'))
        key_row.connect('changed', lambda _: add_key_dialog.set_response_enabled(
            'add', 
            bool(key_row.get_text())))

        if is_bool:
            switch = Gtk.Switch(valign=Gtk.Align.CENTER)
            value_row = Adw.ActionRow(
                title=_('Value'),
                activatable_widget=switch)
            value_row.add_suffix(switch)
        else:
            value_row = Adw.EntryRow(title=_('Value'))

        group = Adw.PreferencesGroup()
        group.add(key_row)
        group.add(value_row)

        add_key_dialog.set_extra_child(group)
        add_key_dialog.connect('response', lambda _, resp: \
            self.add_key(
                key_row.get_text(),
                switch.get_state() if is_bool else value_row.get_text(),
                is_bool) \
            if resp == 'add' \
            else ...)
        add_key_dialog.set_transient_for(self.get_root())
        add_key_dialog.present()

    def add_key(self, key, value, is_bool: bool):
        self.file.appsection.add_entry(key, value)
        self.build_ui()


    @classmethod
    def _update_preferences_group(self, preferences_group: Adw.PreferencesGroup, new_children: list[Gtk.Widget]):
        '''Removes all present children of the group and adds the new ones'''

        listbox = (
            preferences_group
            .get_first_child()  # Main group GtkBox
            .get_last_child()   # GtkBox containing the listbox
            .get_first_child()) # GtkListbox

        old_children: list[Gtk.Widget] = []

        i = 0
        while listbox.get_row_at_index(i) is not None:
            old_children.append(listbox.get_row_at_index(i))
            i += 1

        for c in old_children:
            preferences_group.remove(c)

        for c in new_children:
            preferences_group.add(c)


class BoolRow(Adw.ActionRow):
    def __init__(self, field: Field) -> None:
        self.field = field

        self.switch = Gtk.Switch(
            active=field.as_bool(),
            valign=Gtk.Align.CENTER,
        )
        self.switch.connect('state-set', self.on_state_set)

        super().__init__(
            title=field.key.capitalize(),
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
        
        super().__init__(title=field.key.capitalize())
        self.set_text(field.as_str() or '')
        self.connect('changed', self.on_changed)

    @staticmethod
    def list_from_field_list(fields: list[Field]):
        return [StringRow(f) for f in fields if type(f.get()) == str and not f.locale]

    def on_changed(self, widget):
        self.field.set(self.get_text())

class LocaleStringRow(Adw.EntryRow):
    def __init__(self, field: Field) -> None:
        self.field = field

        locales = [f.locale for f in self.field.localized_fields]
        self.dropdown = Gtk.DropDown.new_from_strings(locales)
        self.dropdown.set_valign(Gtk.Align.CENTER)
        self.dropdown.connect('notify', self.on_dropdown_notify)
        try:
            self.dropdown.set_selected(locales.index(self.field.localize(
                auto_localize_if_no_locale=True, 
                return_unlocalized_as_fallback=False, 
                return_non_existing_key_as_fallback=False).locale))
        except ValueError:
            ...

        super().__init__(title=field.key.capitalize())
        self.add_suffix(self.dropdown)
        self.connect('changed', self.on_changed)

    @staticmethod
    def list_from_field_list(fields: list[Field]):
        return [LocaleStringRow(f) for f in fields if f.localized_fields and not f.locale]

    @property
    def selected_locale(self):
        return self.dropdown.get_selected_item().get_string()

    def on_dropdown_notify(self, widget, value):
        dropdown_value: str = self.selected_locale
        self.set_text(self.field.localize(self.selected_locale).as_str())

    def on_changed(self, widget):
        self.field.localize(self.selected_locale).set(self.get_text())