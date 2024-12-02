#include "pins-desktop-file-private.h"

struct _PinsDesktopFile
{
    GObject parent_instance;
    GKeyFile *user_key_file;
    GKeyFile *system_key_file;
};

G_DEFINE_TYPE (PinsDesktopFile, pins_desktop_file, G_TYPE_OBJECT);

PinsDesktopFile *
pins_desktop_file_new (void)
{
    PinsDesktopFile *desktop_file
        = g_object_new (PINS_TYPE_DESKTOP_FILE, NULL);

    desktop_file->user_key_file = g_key_file_new ();
    desktop_file->system_key_file = g_key_file_new ();

    return desktop_file;
}

PinsDesktopFile *
pins_desktop_file_load_from_file (GFile *system_file)
{
    PinsDesktopFile *desktop_file = pins_desktop_file_new ();

    // TODO

    return desktop_file;
}

static void
pins_desktop_file_dispose (GObject *object)
{
    PinsDesktopFile *self = (PinsDesktopFile *)object;

    // TODO: Dispose of struct members

    G_OBJECT_CLASS (pins_desktop_file_parent_class)->dispose (object);
}

static void
pins_desktop_file_class_init (PinsDesktopFileClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);
}

static void
pins_desktop_file_init (PinsDesktopFile *self)
{
}
