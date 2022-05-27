from gi.repository import Gtk, Gio, Adw, GObject

@Gtk.Template(resource_path='/com/github/fabrialberio/pinapp/apps_view.ui')
class AppsView(Gtk.Box):
    __gtype_name__ = 'AppsView'

    new_file_button = Gtk.Template.Child('new_file_button')

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)

        GObject.type_register(AppsView)
        GObject.signal_new('new-file', AppsView, GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())

        self.new_file_button.connect('clicked', lambda _: self.emit('new-file'))

    def on_new_file(self, button):
        self.emit('new-file')