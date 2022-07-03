from gi.repository import Gtk, Gio, Adw, GObject

from .desktop_entry import DesktopFile

@Gtk.Template(resource_path='/com/github/fabrialberio/pinapp/file_view.ui')
class FileView(Gtk.Box):
    __gtype_name__ = 'FileView'
    
    back_button = Gtk.Template.Child('back_button')
    save_button = Gtk.Template.Child('save_button')
    main_view = Gtk.Template.Child('main_box')

    app_icon = Gtk.Template.Child('app_icon')
    app_name_entry = Gtk.Template.Child('app_name')
    app_comment = Gtk.Template.Child('app_comment')

    strings_group = Gtk.Template.Child('strings_group')
    add_string_button = Gtk.Template.Child('add_string_button')
    bools_group = Gtk.Template.Child('bools_group')
    add_bool_button = Gtk.Template.Child('add_bool_button')

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.file = None

        self.app_name_buffer = Gtk.EntryBuffer()
        self.app_comment_buffer = Gtk.EntryBuffer()

        GObject.type_register(FileView)
        GObject.signal_new('file-back', FileView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
        GObject.signal_new('file-save', FileView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
        GObject.signal_new('file-edit', FileView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())

        GObject.type_register(StringRow)
        #GObject.signal_new('activate', StringRow, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,))

        self.back_button.connect('clicked', lambda _: self.emit('file-back'))
        self.save_button.connect('clicked', lambda _: self.emit('file-save'))

        self.build_ui()

    def load_file(self, file: DesktopFile):
        print(f'Loading file named {file.path.name}')
        self.file = file

        self.app_icon.set_from_icon_name(self.file.icon_name)
        self._update_buffer(self.app_name_buffer, self.file.app_name)
        self._update_buffer(self.app_comment_buffer, self.file.comment)

        self.save_button.set_sensitive(True)

        # TODO: remove the existing group before adding a new one


    def build_ui(self):
        self.app_name_entry.set_buffer(self.app_name_buffer)
        self.app_comment.set_buffer(self.app_comment_buffer)

        self.strings_group.add(StringRow('Buongiorno', True))
        self.bools_group.add(BoolRow('Test'))

    @classmethod
    def _update_buffer(self, buffer: Gtk.EntryBuffer, text: str):
        '''Updates a text buffer with a given text, handling exceptions'''
        try:
            buffer.set_text(text, len(text))
        except TypeError:
            buffer.set_text('', 0)


class StringRow(Adw.ActionRow):
    def __init__(
            self, 
            title: str,
            monospace: bool = False,
        ) -> None:
        # TODO: Replace this with Adw.EntryRow when possible

        super().__init__(
            title=title,
            css_classes = ['monospace'] if monospace else None,
        )

class BoolRow(Adw.ActionRow):
    def __init__(
            self,
            title: str,
            default_state: bool = False
        ) -> None:

        self.switch = Gtk.Switch(
            active=default_state,
            valign=Gtk.Align.CENTER,
        )

        super().__init__(
            title=title,
            activatable_widget=self.switch,
        )
        super().add_suffix(self.switch)