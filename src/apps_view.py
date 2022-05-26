from gi.repository import Gtk, Gio, Adw

@Gtk.Template(resource_path='/com/github/fabrialberio/pinapp/apps_view.ui')
class AppsView(Gtk.Box):
    __gtype_name__ = 'AppsView'

    new_file_button = Gtk.Template.Child('new_file_button')

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)

        self.new_file_button.connect('clicked', self.on_new_file)

    
    def on_new_file(self, button):
        print('New file')