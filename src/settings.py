from gi.repository import Gio


class Settings(Gio.Settings):
    APP_ID = 'com.github.fabrialberio.pinapp'
    APP_FOLDERS_KEY = 'folders'

    def __init__(self):
        Gio.Settings.__init__(self)

    @classmethod
    def new(cls) -> 'Settings':
        """Return a new Settings object"""
        settings = Gio.Settings.new(Settings.APP_ID)
        settings.__class__ = Settings
        return settings