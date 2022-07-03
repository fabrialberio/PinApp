from gi.repository import Gtk, Gio, Adw, GObject

from .desktop_entry import DesktopFile

@Gtk.Template(resource_path='/com/github/fabrialberio/pinapp/file_view.ui')
class FileView(Gtk.Box):
    __gtype_name__ = 'FileView'
    
    back_button = Gtk.Template.Child('back_button')
    save_button = Gtk.Template.Child('save_button')
    
    app_icon = Gtk.Template.Child('app_icon')
    app_name_entry = Gtk.Template.Child('app_name')
    app_comment = Gtk.Template.Child('app_comment')

    main_view = Gtk.Template.Child('main_box')

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
        stringGroup = ValuesGroup(self.file)
        self.main_view.append(stringGroup)

    def build_ui(self):
        self.app_name_entry.set_buffer(self.app_name_buffer)
        self.app_comment.set_buffer(self.app_comment_buffer)

    @classmethod
    def _update_buffer(self, buffer: Gtk.EntryBuffer, text: str):
        '''Updates a text buffer with a given text, handling exceptions'''
        try:
            buffer.set_text(text, len(text))
        except TypeError:
            buffer.set_text('', 0)


class ValuesGroup(Adw.PreferencesGroup):
    
    def __init__(self, 
        file: DesktopFile, 
        type: str = 'string',
    ):
        super().__init__(
            title = f'{type.capitalize()} values',
            description = '',
            header_suffix = Gtk.Button(
                child = Adw.ButtonContent(
                    icon_name = 'list-add',
                    label = 'Add',
                )
            )
        )

        self.file = file
        self.type = type

        self.build_ui()
    
    def build_ui(self):...

class StringRow(Adw.ActionRow):
    def __init__(
        self, 
        title,
        monospace=False,
    ) -> None:

        self.buffer = Gtk.EntryBuffer()
        self.entry = Gtk.Entry(
            buffer=self.buffer,
            css_classes = ['monospace'] if monospace else None,
        )
        
        self.entry.connect('activate', lambda _: self.emit('activate', self.entry.get_text()))

        super().__init__(
            title=title,
            activatable_widget=self.entry,
        )