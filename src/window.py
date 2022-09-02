# window.py
#
# Copyright 2022 Fabri210
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#from apps_view import AppsView

from gi.repository import Gtk, Adw, Gio

from .apps_view import AppsView
from .file_view import FileView

from .desktop_entry import DesktopFile
from pathlib import Path

@Gtk.Template(resource_path='/com/github/fabrialberio/pinapp/window.ui')
class PinAppWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'PinAppWindow'

    leaflet = Gtk.Template.Child('main_leaflet')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.apps_view = AppsView()
        self.apps_view.connect('file-new', self.on_new_file)
        self.apps_view.connect('file-open', self.on_file_open)
        self.leaflet.append(self.apps_view)

        self.file_view = FileView()
        self.file_view.connect('file-back', self.on_file_back)
        self.file_view.connect('file-save', self.on_file_save)
        self.leaflet.append(self.file_view)

    def on_new_file(self, apps_view):
        def callback(widget, response):
            if response == Gtk.ResponseType.ACCEPT:
                path = Path(widget.get_file().get_path())
                
                self.file_view.load_file(DesktopFile.new_with_defaults(path), is_new=True)
                self.leaflet.set_visible_child(self.file_view)

        self.show_file_chooser(
            title=_('Select Folder'),
            action=Gtk.FileChooserAction.SAVE,
            callback=callback,
            accept_label=_('Create'))

    def on_file_back(self, file_view):
        self.leaflet.set_visible_child(self.apps_view)

    def on_file_save(self, file_view: FileView):
        file_view.file.save()
        self.apps_view.build_ui()
        self.leaflet.set_visible_child(self.apps_view)

    def on_file_open(self, file_view, file):
        self.file_view.load_file(file)
        self.leaflet.set_visible_child(self.file_view)

    def show_file_chooser(self, 
            title: str,
            action: Gtk.FileChooserAction, 
            callback: 'function', 
            accept_label: str = None,
            parent: str = None) -> 'Path | None':

        if accept_label == None:
            if action == Gtk.FileChooserAction.OPEN:
                accept_label = _('Open')
            elif action == Gtk.FileChooserAction.SAVE:
                accept_label = _('Save')
            elif action == Gtk.FileChooserAction.SELECT_FOLDER:
                accept_label = _('Select')
            elif action == Gtk.FileChooserAction.CREATE_FOLDER:
                accept_label = _('Select')
        
        dialog = Gtk.FileChooserNative(
            title=title,
            action=action,
            accept_label=accept_label,
            cancel_label=_('Cancel'))

        dialog.connect('response', callback)
        dialog.set_modal(True)
        dialog.set_transient_for(self)
        dialog.show()


    def show_about_window(self):
        builder = Gtk.Builder.new_from_resource('/com/github/fabrialberio/pinapp/about.ui')
        about_window = builder.get_object('about_window')
        about_window.set_transient_for(self)
        about_window.present()