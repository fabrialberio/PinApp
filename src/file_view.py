from typing import Optional, Protocol
from gettext import gettext as _

from gi.repository import Adw, Gtk, GObject # type: ignore

from .desktop_file import DesktopFile, DesktopEntry, Field, FieldType
from .config import set_icon_from_name


class RemoveButton(Gtk.Button):
    __gtype_name__ = 'RemoveButton'

    def __init__(self) -> None:
        super().__init__(
            valign=Gtk.Align.CENTER,
            icon_name='edit-delete-symbolic',
            tooltip_text=_('Remove field'),
        )
        self.add_css_class('flat')

class FieldRow(Protocol):
    file: DesktopFile
    field: Field

    def set_field(self, file: DesktopFile, field: Field) -> None:
        ...

class BoolRow(Adw.ActionRow):
    __gtype_name__ = 'BoolRow'

    file: DesktopFile
    field: Field
    switch: Gtk.Switch
    remove_button: RemoveButton

    def __init__(self) -> None:
        self.switch = Gtk.Switch(
            active=False,
            valign=Gtk.Align.CENTER,
        )
        super().__init__(activatable_widget=self.switch)

        self.remove_button = RemoveButton()
        self.remove_button.connect('clicked', lambda w: self.remove_field())
        self.add_suffix(self.remove_button)
        self.add_suffix(self.switch)

    def set_field(self, file: DesktopFile, field: Field) -> None:
        self.file = file
        self.field = field
        self.set_title(field.key)
        self.switch.set_active(self.file[self.field])

        def update_field(switch: Gtk.Switch, value: bool):
            self.file.set(self.field, value)

        def update_state(file: DesktopFile, field: Field, value: bool):
            if field == self.field and value != self.switch.get_active():
                self.switch.set_active(value)

        self.switch.connect('state-set', update_field)
        file.connect('field-set', update_state)

    def remove_field(self):
        self.file.remove(self.field)

class StringRow(Adw.EntryRow):
    __gtype_name__ = 'StringRow'

    file: DesktopFile
    field: Field
    remove_button: Gtk.Button
    _removable: bool = True

    @GObject.Property(type=bool, default=True)
    def removable(self) -> bool: # type: ignore
        return self._removable
    
    @removable.setter
    def removable(self, value: bool):
        self._removable = value

    def __init__(self, removable: bool=True) -> None:
        super().__init__()

        self._removable = removable
        self.remove_button = RemoveButton()
        self.remove_button.connect('clicked', lambda w: self.remove_field())

        self.connect('changed', lambda w: self.update_remove_button_visible())
        self.add_suffix(self.remove_button)

    def set_field(self, file: DesktopFile, field: Field) -> None:
        self.file = file
        self.field = field
        self.set_title(self.field.key)
        self.set_text(self.file.get(self.field, ''))

        def update_field(widget: StringRow):
            self.file.set(self.field, self.get_text())

        self.connect('changed', update_field)

    def remove_field(self):
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

    def set_field(self, file: DesktopFile, field: Field):
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

            def update_icon(widget: LocaleButton, selected: Optional[str]):
                icon.set_opacity(locale == selected or (selected == None and locale == UNLOCALIZED_STR))

            update_icon(self, self.selected)
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
    locale_field: Field
    locale_select: LocaleButton

    def __init__(self, removable=True) -> None:
        super().__init__(removable)

        self.locale_select = LocaleButton()
        self.locale_select.connect('changed', lambda w, l: self.set_locale(l))
        self.add_suffix(self.locale_select)

    def set_field(self, file: DesktopFile, field: Field) -> None:
        self.locale_field = field
        
        super().set_field(file, field.localize(None))
        self.locale_select.set_field(file, field)
        self.set_locale(None)

    def set_locale(self, locale: Optional[str]):
        self.locale = locale
        self.field = self.locale_field.localize(locale)
        self.set_text(self.file.get(self.field, ''))
        self.update_remove_button_visible()

    def remove_field(self):
        self.file.remove(self.field)

        if self.locale is not None and self.file.locales(self.locale_field):
            self.locale_select.set_selected(None)
            #self.locale_select.set_field(self.file, self.locale_field)

    def update_remove_button_visible(self):
        if self.locale is not None:
            self.remove_button.set_visible(not self.get_text())
        elif self.locale is None and self.removable and not self.file.locales(self.locale_field):
            self.remove_button.set_visible(not self.get_text())
        else:
            self.remove_button.set_visible(False)

@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/dialog_add_field.ui')
class AddFieldDialog(Adw.MessageDialog):
    __gtype_name__ = 'AddFieldDialog'

    type_combo_row: Adw.ComboRow = Gtk.Template.Child()
    key_entry = Gtk.Template.Child()
    locale_entry = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        def on_type_selected(row: Adw.ComboRow, pspec: GObject.ParamSpec):
            self.locale_entry.set_visible(self.type_combo_row.get_selected() == 2)

        def update_response_enabled(widget: AddFieldDialog):
            enabled = bool(self.key_entry.get_text())
            
            if self.type_combo_row.get_selected() == 2:
                enabled = enabled and bool(self.locale_entry.get_text())

            self.set_response_enabled('add', enabled)

        def on_response(widget: AddFieldDialog, resp: str):
            if resp == 'add':
                key = self.key_entry.get_text()

                if self.type_combo_row.get_selected() == 0:
                    self.emit('add', Field(DesktopEntry.group, key, FieldType.BOOL), None)
                elif self.type_combo_row.get_selected() == 1:
                    self.emit('add', Field(DesktopEntry.group, key, FieldType.STRING), None)
                else:
                    self.emit(
                        'add',
                        Field(DesktopEntry.group, key, FieldType.LOCALIZED_STRING),
                        self.locale_entry.get_text()
                    )

        self.type_combo_row.connect('notify::selected', on_type_selected)
        self.key_entry.connect('changed', update_response_enabled)
        self.locale_entry.connect('changed', update_response_enabled)
        self.connect('response', on_response)

GObject.signal_new('add', AddFieldDialog, GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT,))

@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/file_view.ui')
class FileView(Adw.BreakpointBin):
    __gtype_name__ = 'FileView'

    file: DesktopFile
    field_row_map: dict[Field, FieldRow] = {}

    scrolled_window: Gtk.ScrolledWindow = Gtk.Template.Child()
    icon: Gtk.Image = Gtk.Template.Child()
    name_row: LocaleStringRow = Gtk.Template.Child()
    comment_row: LocaleStringRow = Gtk.Template.Child()
    fields_listbox: Adw.PreferencesGroup = Gtk.Template.Child()
    add_field_button: Gtk.Button = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        self.add_field_button.connect('clicked', lambda b: self.show_add_field_dialog())
        
    def set_file(self, file: DesktopFile):
        self.file = file

        set_icon_from_name(self.icon, self.file.get(DesktopEntry.ICON, ''))

        self.name_row.set_field(self.file, DesktopEntry.NAME)
        self.comment_row.set_field(self.file, DesktopEntry.COMMENT)

        def match_field(item: Field) -> bool:            
            if item in [DesktopEntry.NAME, DesktopEntry.COMMENT]:
                return False

            if item.locale() is not None:
                if item.localize(None) in file.fields:
                    return False

            return True

        def create_row(field: Field) -> FieldRow:
            if field.localize(None) in DesktopEntry.fields:
                index = DesktopEntry.fields.index(field.localize(None))
                field.field_type = DesktopEntry.fields[index].field_type

            if self.file.locales(field):
                field.field_type = FieldType.LOCALIZED_STRING

            match field.field_type:
                case FieldType.BOOL:
                    row = BoolRow()
                case FieldType.STRING | FieldType.STRING_LIST:
                    row = StringRow()
                    field.field_type = FieldType.STRING
                case FieldType.LOCALIZED_STRING | FieldType.LOCALIZED_STRING_LIST:
                    row = LocaleStringRow()
                    field.field_type = FieldType.LOCALIZED_STRING
            
            if field == DesktopEntry.ICON:
                button = Gtk.Button(
                    valign=Gtk.Align.CENTER,
                    icon_name='folder-open-symbolic',
                    tooltip_text=_('Choose icon')
                )
                button.add_css_class('flat')

                def update_icon(row: StringRow):
                    set_icon_from_name(self.icon, row.get_text())

                def show_choose_icon_dialog(button: Gtk.Button):
                    # TODO
                    print('Imagine a file picker just appeared')

                button.connect('clicked', show_choose_icon_dialog)
                row.connect('changed', update_icon)
                row.add_suffix(button)

            if field in [DesktopEntry.EXEC, DesktopEntry.TYPE]:
                row.removable = False

            row.set_field(file, field)
            return row

        self.fields_listbox.bind_model(Gtk.FilterListModel.new(
            self.file.fields, Gtk.CustomFilter.new(match_field)),
            create_row
        )

    def show_add_field_dialog(self):
        dialog = AddFieldDialog()

        def add_field(widget: AddFieldDialog, field: Field, locale: str):
            if field.field_type in (FieldType.LOCALIZED_STRING, FieldType.LOCALIZED_STRING_LIST):
                if locale is not None:
                    if field not in self.file.fields:
                        self.file.set(field, field.default_value())
                    field = field.localize(locale)

            self.file.set(field, field.default_value())
            self.set_file(self.file)

        dialog.connect('add', add_field)
        dialog.set_transient_for(self.get_root())
        dialog.present()
