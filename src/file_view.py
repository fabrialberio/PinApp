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

class LocaleButton(Gtk.MenuButton):
    __gtype_name__ = 'LocaleSelectButton'

    selected: Optional[str] = None

    def __init__(self, file: DesktopFile, field: LocaleField[str]) -> None:
        button_content = Adw.ButtonContent(
            icon_name='preferences-desktop-locale-symbolic'
        )
        popover = Gtk.Popover()
        popover.add_css_class('menu')

        super().__init__(
            valign=Gtk.Align.CENTER,
            child=button_content,
            popover=popover,
        )
        self.add_css_class('flat')

        UNLOCALIZED_STR = _('(Unlocalized)')
        items = [UNLOCALIZED_STR] + file.locales(field)

        def setup_item(factory: Gtk.SignalListItemFactory, item: Gtk.ListItem):
            child = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            child.append(Gtk.Label(
                max_width_chars=20,
                valign=Gtk.Align.CENTER
            ))
            child.append(Gtk.Image(icon_name='object-select-symbolic'))
            item.set_child(child)

        def bind_item(factory: Gtk.SignalListItemFactory, item: Gtk.ListItem):
            label = item.get_child().get_first_child()
            label.set_label(item.get_item().get_string())

            icon = item.get_child().get_last_child()
            locale = item.get_item().get_string() 

            if locale == self.selected or (self.selected == None and locale == UNLOCALIZED_STR):
                icon.set_visible(True)
            else:
                icon.set_visible(False)

            def update_icon(widget: LocaleButton, selected: Optional[str]):
                icon.set_visible(locale == selected or (selected == None and locale == UNLOCALIZED_STR))

            self.connect('changed', update_icon)

        factory = Gtk.SignalListItemFactory()
        factory.connect('setup', setup_item)
        factory.connect('bind', bind_item)

        def item_selected(list_view: Gtk.ListView, index: int):
            self.set_selected(items[index] if index > 0 else None)
            popover.popdown()

        list_view = Gtk.ListView(
            single_click_activate=True,
            model=Gtk.SingleSelection.new(Gtk.StringList.new(items)),
            factory=factory
        )
        list_view.connect('activate', item_selected)

        popover.set_child(Gtk.ScrolledWindow(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            max_content_height=400,
            propagate_natural_width=True,
            propagate_natural_height=True,
            child=list_view
        ))

        def update_label(widget: LocaleButton, selected: Optional[str]):
            if selected is not None:
                button_content.set_label(selected)
            else:
                button_content.set_label('')

        self.connect('changed', update_label)

    def set_selected(self, locale: Optional[str]):
        self.selected = locale
        self.emit('changed', locale)

GObject.signal_new('changed', LocaleButton, GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,))

class LocaleStringRow(Adw.EntryRow):
    __gtype_name__ = 'LocaleStringRow'

    file: DesktopFile
    field: LocaleField[str]
    locale: Optional[str] = None

    def __init__(self) -> None:
        super().__init__()

    def set_field(self, file: DesktopFile, field: LocaleField[str]) -> None:
        self.set_title(field.key)

        self.file = file
        self.field = LocaleField(field.group, field.key, str)

        locale_select = LocaleButton(file, field)
        locale_select.connect('changed', lambda w, l: self.set_locale(l))
        self.add_suffix(locale_select)

        self.set_locale(None)

        def update_field(widget: StringRow):
            file.set(self.field.localize(self.locale), self.get_text(), emit=False)

        def update_text(file: DesktopFile, field_: Field[str], value: str):
            if field_ == self.field.localize(self.locale) and value != self.get_text():
                self.set_text(value)

        self.connect('changed', update_field)
        file.connect('field-set', update_text)

    def set_locale(self, locale: Optional[str]):
        self.locale = locale
        self.set_text(self.file.get(self.field.localize(locale), ''))


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

        def update_icon(row: StringRow):
            print('update_icon', self.icon_row.get_text())
            set_icon_from_name(self.icon, self.icon_row.get_text())

        self.icon_row.connect('changed', update_icon)

        for field in self.file.fields(DesktopEntry.group):
            if field in [DesktopEntry.ICON, DesktopEntry.NAME, DesktopEntry.COMMENT]:
                continue

            if field in DesktopEntry.fields:
                field = next(f for f in DesktopEntry.fields if f.key == field.key)

            if field._type == bool:
                row = BoolRow()
                row.set_field(self.file, field) # type: ignore
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