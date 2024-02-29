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
            file.set(field, value)

        def update_state(file: DesktopFile, field_: Field[bool], value: bool):
            if field_ == field and value != self.switch.get_active():
                self.switch.set_active(value)

        self.switch.connect('state-set', update_field)
        file.connect('field-set', update_state)

class StringRow(Adw.EntryRow):
    __gtype_name__ = 'StringRow'

    file: DesktopFile
    field: Field[str]
    remove_button: Gtk.Button
    _removable: bool = True

    @GObject.Property(type=bool, default=True)
    def removable(self) -> bool: # type: ignore
        return self._removable
    
    @removable.setter
    def removable(self, value: bool):
        self._removable = value

    def __init__(self, removable: bool=True) -> None:
        self._removable = removable

        super().__init__()

        self.remove_button = Gtk.Button(
            valign=Gtk.Align.CENTER,
            visible=False,
            icon_name='edit-delete-symbolic',
            tooltip_text=_('Remove field'),
        )
        self.remove_button.add_css_class('flat')
        self.remove_button.connect('clicked', lambda w: self.remove_field())
        self.connect('changed', lambda w: self.update_remove_button_visible())
        self.add_suffix(self.remove_button)

    def set_field(self, file: DesktopFile, field: Field[str]) -> None:
        self.file = file
        self.field = field

        self.set_title(field.key)
        self.set_text(file.get(field, ''))

        def update_field(widget: StringRow):
            file.set(self.field, self.get_text())

        self.connect('changed', update_field)

    def remove_field(self):
        self.set_visible(False)
        self.file.remove(self.field)

    def update_remove_button_visible(self):
        if self.removable:
            self.remove_button.set_visible(not self.get_text())
        else:
            self.remove_button.set_visible(False)


class LocaleButton(Gtk.MenuButton):
    __gtype_name__ = 'LocaleSelectButton'

    popover: Gtk.Popover
    selected: Optional[str] = None

    def __init__(self) -> None:
        button_content = Adw.ButtonContent(
            icon_name='preferences-desktop-locale-symbolic'
        )
        self.popover = Gtk.Popover()
        self.popover.add_css_class('menu')

        super().__init__(
            child=button_content,
            valign=Gtk.Align.CENTER,
            popover=self.popover,
            tooltip_text=_('Select locale'),
        )
        self.add_css_class('flat')

        def update_label(widget: LocaleButton, selected: Optional[str]):
            if selected is not None:
                button_content.set_label(selected)
            else:
                button_content.set_label('')

        self.connect('changed', update_label)

    def set_field(self, file: DesktopFile, field: LocaleField):
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
            self.popover.popdown()

        list_view = Gtk.ListView(
            single_click_activate=True,
            model=Gtk.SingleSelection.new(Gtk.StringList.new(items)),
            factory=factory
        )
        list_view.connect('activate', item_selected)

        self.popover.set_child(Gtk.ScrolledWindow(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            max_content_height=400,
            propagate_natural_width=True,
            propagate_natural_height=True,
            child=list_view
        ))

    def set_selected(self, locale: Optional[str]):
        self.selected = locale
        self.emit('changed', locale)

GObject.signal_new('changed', LocaleButton, GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,))

class LocaleStringRow(StringRow):
    __gtype_name__ = 'LocaleStringRow'

    locale: Optional[str] = None
    locale_field: LocaleField[str]
    locale_select: LocaleButton

    def __init__(self, removable: bool=True) -> None:
        super().__init__(removable)

        self.locale_select = LocaleButton()
        self.locale_select.connect('changed', lambda w, l: self.set_locale(l))
        self.add_suffix(self.locale_select)

    def set_field(self, file: DesktopFile, field: LocaleField) -> None:
        super().set_field(file, field.localize(None))
        self.locale_select.set_field(file, field)

        self.locale_field = LocaleField(field.group, field.key, str)
        self.set_locale(None)

    def set_locale(self, locale: Optional[str]):
        self.locale = locale
        self.field = self.locale_field.localize(locale)
        self.set_text(self.file.get(self.field, ''))
        self.update_remove_button_visible()

    def remove_field(self):
        self.file.remove(self.field)

        if self.locale is None and not self.file.locales(self.locale_field):
            self.set_visible(False)
        else:
            self.locale_select.set_selected(None)
            self.locale_select.set_field(self.file, self.locale_field)

    def update_remove_button_visible(self):
        if self.removable and self.locale is not None:
            self.remove_button.set_visible(not self.get_text())
        elif self.removable and self.locale is None and not self.file.locales(self.locale_field):
            self.remove_button.set_visible(not self.get_text())
        else:
            self.remove_button.set_visible(False)

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
    add_field_button: Gtk.Button = Gtk.Template.Child()

    def __init__(self, file: DesktopFile):
        super().__init__()

        self.file = file

        set_icon_from_name(self.icon, self.file.get(DesktopEntry.ICON, ''))

        self.icon_row.set_field(self.file, DesktopEntry.ICON)
        self.name_row.set_field(self.file, DesktopEntry.NAME)
        self.comment_row.set_field(self.file, DesktopEntry.COMMENT)

        def update_icon(row: StringRow):
            set_icon_from_name(self.icon, self.icon_row.get_text())

        self.icon_row.connect('changed', update_icon)

        for field in self.file.fields(DesktopEntry.group):
            if field in [DesktopEntry.ICON, DesktopEntry.NAME, DesktopEntry.COMMENT]:
                continue

            if field in DesktopEntry.fields:
                field = next(f for f in DesktopEntry.fields if f == field)

            if field._type == bool:
                row = BoolRow()
                row.set_field(self.file, field) # type: ignore
            elif isinstance(field, LocaleField):
                row = LocaleStringRow()
                row.set_field(self.file, LocaleField(field.group, field.key, str))
            else:
                row = StringRow()

                if field == DesktopEntry.TYPE:
                    row.removable = False

                row.set_field(self.file, Field(field.group, field.key, str))

            self.values_group.add(row)

        def on_add_field(button: Gtk.Button):
            self.show_add_field_dialog()

        self.add_field_button.connect('clicked', on_add_field)

    def show_add_field_dialog(self):
        return
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

    def remove_field(self, field: Field):
        ...