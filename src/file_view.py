from typing import Optional
from gettext import gettext as _

from gi.repository import Adw, Gtk, Gio, GObject # type: ignore

from .desktop_file import DesktopFile, DesktopEntry, Field
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


class StringRow(Adw.EntryRow):
    __gtype_name__ = 'StringRow'

    file: DesktopFile
    field: Field
    remove_button: Gtk.Button
    _removable: bool = True
    _previous_value: str

    @GObject.Property(type=bool, default=True)
    def removable(self) -> bool:
        return self._removable and self.file.has_field(self.field)
    
    @removable.setter
    def set_removable(self, value: bool):
        self._removable = value

    def __init__(self, removable: bool=True) -> None:
        super().__init__()

        self._removable = removable
        self.remove_button = RemoveButton()
        self.remove_button.connect('clicked', self._on_remove_button_clicked)

        self.add_suffix(self.remove_button)

    def set_field(self, file: DesktopFile, field: Field) -> None:
        self.file = file
        self.field = field
        self._previous_value = self.file.get_str(self.field)

        self.set_title(self.field.key)
        self.set_text(self.file.get_str(self.field))

        self.connect('changed', lambda e: self._update_appearance())
        self.file.connect('field-set', self._on_field_set)
        self._update_appearance()

    def _on_remove_button_clicked(self, _button: Gtk.Button):
        self.file.remove(self.field)

    def _on_field_set(self, _file: DesktopFile, field: Field, _value: str):
        if field == self.field:
            self._update_appearance()

    def _update_appearance(self):
        current_value = self.file.get_str(self.field, None)

        if current_value is None:                                       # Field does not exist
            self.file.set_str(self.field, self.get_text())
            self._previous_value = self.get_text()
        elif self._previous_value == current_value == self.get_text():  # Everything is up-to-date
            ...
        elif self._previous_value == self.get_text():                   # Field has been changed externally
            self.set_text(current_value)
            self._previous_value = current_value
        elif self._previous_value == current_value:                     # Text has been changed by user
            self.file.set_str(self.field, self.get_text())
            self._previous_value = self.get_text()

        self.remove_button.set_visible(self.set_removable and not self.get_text())


class BoolOrStringRow(StringRow):
    __gtype_name__ = 'BoolOrStringRow'

    switch: Gtk.Switch
    _previous_bool_value: bool

    def __init__(self, removable: bool = True) -> None:
        super().__init__(removable)

        self.switch = Gtk.Switch(
            valign=Gtk.Align.CENTER,
            visible=False,
        )
        self.add_suffix(self.switch)

    def set_field(self, file: DesktopFile, field: Field) -> None:
        self._previous_bool_value = file.get_bool(field)        
        self.switch.set_active(file.get_bool(field))
        
        super().set_field(file, field)  

        self.switch.connect('state-set', lambda s, v: self._update_appearance())
        self._update_appearance()

    def _update_appearance(self):
        super()._update_appearance()

        current_bool_value = self.file.get_bool(self.field, None)

        if current_bool_value is None:                                                      # Field is not boolean
            ...
        elif current_bool_value == self._previous_bool_value == self.switch.get_active():   # Everything is up-to-date
            ...
        elif self._previous_bool_value == self.switch.get_active():                         # Field has been changed externally
            self.switch.set_active(current_bool_value)
            self._previous_bool_value = current_bool_value
        elif self._previous_bool_value == current_bool_value:                               # Switch has been changed by user
            self.file.set_bool(self.field, self.switch.get_active())
            self._previous_bool_value = self.switch.get_active()

        self.switch.set_visible(current_bool_value is not None)
        self.remove_button.set_visible(self.set_removable and (self.switch.get_visible() or not self.get_text()))


class LocaleButton(Gtk.MenuButton):
    __gtype_name__ = 'LocaleButton'

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
        if locale != self.selected:
            self.selected = locale
            self.emit('changed', locale)

GObject.signal_new('changed', LocaleButton, GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,))


class FieldRow(BoolOrStringRow):
    __gtype_name__ = 'FieldRow'

    locale: Optional[str] = None
    locale_select: LocaleButton
    unlocalized_field: Field

    def __init__(self, removable=True) -> None:
        super().__init__(removable)

        self.locale_select = LocaleButton()
        self.locale_select.connect('changed', lambda w, l: self.set_locale(l))
        self.add_suffix(self.locale_select)

    def set_field(self, file: DesktopFile, field: Field) -> None:
        self.unlocalized_field = field.localize(None)

        super().set_field(file, self.unlocalized_field)

        self.locale_select.set_field(file, self.unlocalized_field)
        self.locale_select.set_selected(file.localize_current(self.unlocalized_field).locale())
        self._update_appearance()

    def set_locale(self, locale: Optional[str]):
        self.locale = locale
        self.field = self.unlocalized_field.localize(locale)
        self._update_appearance()

    def _on_remove_button_clicked(self, _button: Gtk.Button):
        self.file.remove(self.field)
        self.locale_select.set_field(self.file, self.field)
        self.locale_select.set_selected(None)

    def _on_field_set(self, _file: DesktopFile, field: Field, _value: str):
        super()._on_field_set(_file, field, _value)

        if field.locale() is not None and field.localize(None) == self.unlocalized_field:
            self.locale_select.set_field(self.file, self.unlocalized_field)
            self._update_appearance()

    def _update_appearance(self):
        super()._update_appearance()

        self.locale_select.set_visible(self.file.locales(self.field))

        if self.locale is not None and (not self.get_text() or self.switch.get_visible()):
            self.remove_button.set_visible(True)
        elif self.locale is None and self.locale_select.get_visible():
            self.remove_button.set_visible(False)


@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/dialog_add_field.ui')
class AddFieldDialog(Adw.MessageDialog):
    __gtype_name__ = 'AddFieldDialog'

    key_entry = Gtk.Template.Child()
    locale_entry = Gtk.Template.Child()


@Gtk.Template(resource_path='/io/github/fabrialberio/pinapp/file_view.ui')
class FileView(Adw.BreakpointBin):
    __gtype_name__ = 'FileView'

    file: DesktopFile

    scrolled_window: Gtk.ScrolledWindow = Gtk.Template.Child()
    icon: Gtk.Image = Gtk.Template.Child()
    name_row: FieldRow = Gtk.Template.Child()
    comment_row: FieldRow = Gtk.Template.Child()
    hidden_toggle: Gtk.ToggleButton = Gtk.Template.Child()
    terminal_toggle: Gtk.ToggleButton = Gtk.Template.Child()
    fields_listbox: Adw.PreferencesGroup = Gtk.Template.Child()
    add_field_button: Adw.ButtonRow = Gtk.Template.Child()

    def __init__(self, file: DesktopFile):
        super().__init__()

        self.set_file(file)
        self.add_field_button.connect('activated', lambda b: self.show_add_field_dialog())
        
    def set_file(self, desktop_file: DesktopFile):
        self.file = desktop_file

        set_icon_from_name(self.icon, self.file.get_str(DesktopEntry.ICON))
        self._connect_toggle(self.hidden_toggle, DesktopEntry.NO_DISPLAY)
        self._connect_toggle(self.terminal_toggle, DesktopEntry.TERMINAL)

        self.name_row.set_field(self.file, DesktopEntry.NAME)
        self.comment_row.set_field(self.file, DesktopEntry.COMMENT)

        def match_field(item: Field) -> bool:            
            if item in [DesktopEntry.NAME, DesktopEntry.COMMENT]:
                return False

            if item.locale() is not None:
                if item.localize(None) in self.file.fields:
                    return False

            return True

        def create_row(field: Field) -> StringRow:
            row = FieldRow()

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
                row.set_removable = False

            row.set_field(desktop_file, field)
            return row

        self.fields_listbox.bind_model(Gtk.FilterListModel.new(
            self.file.fields, Gtk.CustomFilter.new(match_field)),
            create_row
        )

    def save_file(self, gfile: Gio.File):
        self.file.write_to_path(gfile.get_path())

    def show_add_field_dialog(self):
        dialog = AddFieldDialog()

        def update_response_enabled(_dialog: Adw.MessageDialog):
            dialog.set_response_enabled('add', dialog.key_entry.get_text())

        def add_field(dialog: Adw.MessageDialog, _resp: str):
            field = Field(DesktopEntry.group, dialog.key_entry.get_text())
            locale = dialog.locale_entry.get_text() or None
            self.file.set_str(field.localize(locale), '')

        dialog.connect('response', add_field)
        dialog.key_entry.connect('changed', update_response_enabled)
        dialog.set_transient_for(self.get_root())
        dialog.present()

    def _connect_toggle(self, button: Gtk.ToggleButton, field: Field):
        def update_field(button: Gtk.ToggleButton):
            self.file.set_bool(field, button.get_active())

        def update_style(button: Gtk.ToggleButton, pspec: GObject.ParamSpec):
            # TODO: Replace with accent to support custom accent colors
            if button.get_active():
                button.add_css_class('pill-toggle-active')
            else:
                button.remove_css_class('pill-toggle-active')

        def update_toggled(file: DesktopFile, field_: Field, value_: bool = False):
            if field_ == field:
                button.set_active(self.file.get_bool(field))

        update_toggled(self.file, field, False)
        update_style(button, None)
        button.connect('toggled', update_field)
        button.connect('notify::active', update_style)
        self.file.connect('field-set', update_toggled)
        self.file.connect('field-removed', update_toggled)
