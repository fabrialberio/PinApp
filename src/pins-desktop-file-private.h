#pragma once

#include <gio/gio.h>

G_BEGIN_DECLS

#define PINS_TYPE_DESKTOP_FILE (pins_desktop_file_get_type ())

G_DECLARE_FINAL_TYPE (PinsDesktopFile, pins_desktop_file, PINS, DESKTOP_FILE,
                      GObject);

PinsDesktopFile *pins_desktop_file_load_from_file (GFile *file,
                                                   GError **error);
void pins_desktop_file_save (PinsDesktopFile *self, GError **error);

gboolean pins_desktop_file_get_boolean (PinsDesktopFile *self,
                                        const gchar *key, GError **error);
gchar *pins_desktop_file_get_string (PinsDesktopFile *self, const gchar *key,
                                     GError **error);
gchar *pins_desktop_file_get_locale_string (PinsDesktopFile *self,
                                            const gchar *key,
                                            const gchar *locale,
                                            GError **error);
void pins_desktop_file_set_boolean (PinsDesktopFile *self, const gchar *key,
                                    const gboolean value);
void pins_desktop_file_set_string (PinsDesktopFile *self, const gchar *key,
                                   const gchar *value);
void pins_desktop_file_set_locale_string (PinsDesktopFile *self,
                                          const gchar *key, gchar *value,
                                          const gchar *locale);

gboolean pins_desktop_file_is_key_resettable (PinsDesktopFile *self,
                                              const gchar *key);
void pins_desktop_file_reset_key (PinsDesktopFile *self, const gchar *key);

G_END_DECLS
