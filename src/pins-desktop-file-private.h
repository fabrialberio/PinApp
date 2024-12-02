#pragma once

#include <gio/gio.h>

G_BEGIN_DECLS

#define PINS_TYPE_DESKTOP_FILE (pins_desktop_file_get_type ())

G_DECLARE_FINAL_TYPE (PinsDesktopFile, pins_desktop_file, PINS, DESKTOP_FILE,
                      GObject);

PinsDesktopFile *pins_desktop_file_new (void);
PinsDesktopFile *pins_desktop_file_load_from_file (GFile *system_file);

gboolean pins_desktop_file_get_boolean (const gchar *key, GError **error);
gchar *pins_desktop_file_get_string (const gchar *key, GError **error);
gchar *pins_desktop_file_get_locale_string (const gchar *key, gchar *locale,
                                            GError **error);
void pins_desktop_file_set_boolean (const gchar *key, const gboolean value);
void pins_desktop_file_set_string (const gchar *key, const gchar *value);
void pins_desktop_file_set_locale_string (const gchar *key, gchar *value,
                                          gchar *locale);

void pins_desktop_file_reset_key (const gchar *key);

gchar **pins_desktop_file_locales (void);

void pins_desktop_file_save (GError **error);

G_END_DECLS
