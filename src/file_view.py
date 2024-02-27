from typing import Protocol, Optional, get_origin
from gettext import gettext as _

from gi.repository import Adw, Gtk, GObject # type: ignore

from .desktop_file import DesktopFile, DesktopEntry, Field, LocaleField
from .config import set_icon_from_name


def update_pref_group(group: Adw.PreferencesGroup, rows: list[Gtk.Widget]):
    group.get_first_child().get_last_child().get_first_child().remove_all()

    for row in rows:
        group.add(row)


class FieldRow(Protocol):
    def set_field(self, file: DesktopFile, field: Field) -> None:
        ...

class BoolRow(Adw.ActionRow):
    __gtype_name__ = 'BoolRow'

    switch: Gtk.Switch

    def __init__(self) -> None:
        self.switch = Gtk.Switch(
            active=False,
            valign=Gtk.Align.CENTER,
        )

        super().__init__(activatable_widget=self.switch)
        self.add_suffix(self.switch)

    def set_field(self, file: DesktopFile, field: Field[bool]) -> None:
        self.set_title(field.key)
        self.switch.set_active(file[field])

        def update_field(self, value: bool):
            file.set(field, value, emit=False)

        def update_state(file: DesktopFile, field_: Field[bool], value: bool):
            if field_ == field and value != self.switch.get_active():
                self.switch.set_active(value)

        self.switch.connect('state-set', update_field)
        file.connect('field-set', update_state)

class StringRow(Adw.EntryRow):
    __gtype_name__ = 'StringRow'

    def __init__(self) -> None:
        super().__init__()
    
    def set_field(self, file: DesktopFile, field: Field[str]) -> None:
        self.set_title(field.key)
        self.set_text(file.get(field, ''))

        def update_field(widget: StringRow):
            file.set(field, self.get_text(), emit=False)

        def update_text(file: DesktopFile, field_: Field[str], value: str):
            if field_ == field and value != self.get_text():
                self.set_text(value)

        self.connect('changed', update_field)
        file.connect('field-set', update_text)

class LocaleStringRow(Adw.EntryRow):
    __gtype_name__ = 'LocaleStringRow'

    file: DesktopFile
    field: LocaleField[str]
    locale: Optional[str] = None
    locale_select: Gtk.MenuButton

    def __init__(self) -> None:
        super().__init__()

        self.locale_select = Gtk.MenuButton(
            icon_name='preferences-desktop-locale-symbolic'
        )
        self.add_suffix(self.locale_select)

    def set_field(self, file: DesktopFile, field: LocaleField[str]) -> None:
        self.set_title(field.key)

        self.file = file
        self.field = LocaleField(field.group, field.key, str)
        #self.locale_select.set_popover(Gtk.PopoverMenu.new_from_model())

        self.set_locale(None)

        def update_field(widget: StringRow):
            file.set(self.field, self.get_text(), emit=False)

        def update_text(file: DesktopFile, field_: Field[str], value: str):
            if field_ == self.field.localize(self.locale) and value != self.get_text():
                self.set_text(value)

        self.connect('changed', update_field)
        file.connect('field-set', update_text)

    def set_locale(self, locale: Optional[str]):
        self.locale = locale
        self.set_title(self.field.localize(locale).key) 
        self.set_text(self.file.get(self.field.localize(locale), ''))

class LocaleStringsGroup(Adw.PreferencesGroup):
    __gtype_name__ = 'LocaleStringsGroup'

    def __init__(self) -> None:
        super().__init__()
        self.set_title(_('Localized values'))

    def set_fields(self, file: DesktopFile, fields: list[LocaleField]):        
        locales = sorted(list(set([l for f in fields for l in file.locales(f)])))
        
        if not locales:
            raise ValueError('Tried to set fields for a group with no locales.')

        locale_chooser_row = Adw.ComboRow(
            title=_('Locale'),
            model=Gtk.StringList.new(locales)
        )
        locale_chooser_row.add_prefix(Gtk.Image(icon_name='preferences-desktop-locale-symbolic'))
        
        rows = []
        for f in fields:
            row = LocaleStringRow()
            row.set_field(file, f, locale_chooser_row.get_selected_item().get_string())
            rows.append(row)

        update_pref_group(self, [locale_chooser_row] + rows)

        def update_rows(widget: LocaleStringsGroup, pspec: GObject.ParamSpec):
            if pspec.name == 'selected':
                for row in rows:
                    row.set_locale(locale_chooser_row.get_selected_item().get_string())

        locale_chooser_row.connect('notify', update_rows)

@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/file_view.ui')
class FileView(Adw.BreakpointBin):
    __gtype_name__ = 'FileView'

    file: DesktopFile

    scrolled_window = Gtk.Template.Child()
    compact_breakpoint = Gtk.Template.Child()
    icon: Gtk.Image = Gtk.Template.Child()
    name_row: LocaleStringRow = Gtk.Template.Child()
    comment_row: LocaleStringRow = Gtk.Template.Child()
    icon_row: StringRow = Gtk.Template.Child()
    values_group: Adw.PreferencesGroup = Gtk.Template.Child()

    def __init__(self, file: DesktopFile):
        super().__init__()

        self.file = file

        set_icon_from_name(self.icon, self.file.get(DesktopEntry.ICON, ''))

        self.icon_row.set_field(self.file, DesktopEntry.ICON)
        self.name_row.set_field(self.file, DesktopEntry.NAME)
        self.comment_row.set_field(self.file, DesktopEntry.COMMENT)

        rows: list[FieldRow] = []

        for field in self.file.fields(DesktopEntry.group):
            if field in [DesktopEntry.ICON, DesktopEntry.NAME, DesktopEntry.COMMENT]:
                continue

            if field in DesktopEntry.fields:
                field = next(f for f in DesktopEntry.fields if f.key == field.key)

            if field._type == bool:
                row = BoolRow()
                row.set_field(self.file, field)
            elif isinstance(field, LocaleField):
                row = LocaleStringRow()
                row.set_field(self.file, LocaleField(field.group, field.key, str))
            else:
                row = StringRow()
                row.set_field(self.file, Field(field.group, field.key, str))

            self.values_group.add(row)

    '''
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

                self.REMOVEMEupdate_page()

        add_key_dialog.connect('response', callback)
        add_key_dialog.set_transient_for(self.get_root())
        add_key_dialog.present()
    '''

    def add_row(self):
        ...

    def remove_row(self, field: Field):
        ...