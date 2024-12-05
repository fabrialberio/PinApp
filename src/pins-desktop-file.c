/* pins-desktop-file.c
 *
 * Copyright 2024 Fabrizio
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "pins-desktop-file.h"
#include "pins-directories.h"

#define DEFAULT_FILENAME "pinned-app"
#define KEY_FILE_FLAGS                                                        \
    (G_KEY_FILE_KEEP_COMMENTS | G_KEY_FILE_KEEP_TRANSLATIONS)

struct _PinsDesktopFile
{
    GObject parent_instance;
    GFile *user_file;
    GKeyFile *user_key_file;
    GKeyFile *system_key_file;
};

G_DEFINE_TYPE (PinsDesktopFile, pins_desktop_file, G_TYPE_OBJECT);

/**
 * Given a `GFile`, it constructs a `PinsDesktopFile` with the following logic:
 *  - If the file is in the system folder and a file with the same name is
 *    found in the user folder (`USER_APPS_DIR`), `PinsDesktopFile` is created
 *    with both a user and a system `GKeyFile`;
 *  - If the file is in the system folder and no file with the same name is
 *    found in the user folder, `PinsDesktopFile` is created without a user
 *    `GKeyFile`;
 *  - If the file is in the user folder, `PinsDesktopFile` is created without
 *    a system `GKeyFile`.
 *
 * It is assumed that `file` exists.
 */
PinsDesktopFile *
pins_desktop_file_new_from_file (GFile *file, GError **error)
{
    PinsDesktopFile *desktop_file;
    gboolean file_is_user_file;
    gint retval;

    desktop_file = g_object_new (PINS_TYPE_DESKTOP_FILE, NULL);
    desktop_file->user_key_file = g_key_file_new ();
    desktop_file->system_key_file = g_key_file_new ();

    file_is_user_file = g_file_equal (
        g_file_get_parent (file), g_file_new_for_path (pins_user_app_path ()));

    if (file_is_user_file)
        {
            desktop_file->user_file = file;
            desktop_file->system_key_file = g_key_file_new ();
        }
    else
        {
            desktop_file->user_file = g_file_new_for_path (g_strconcat (
                pins_user_app_path (), g_file_get_basename (file), NULL));

            if (!g_key_file_load_from_file (desktop_file->system_key_file,
                                            g_file_get_path (file),
                                            KEY_FILE_FLAGS, error))
                {
                    g_clear_object (&desktop_file);

                    return NULL;
                }
        }
    g_key_file_load_from_file (desktop_file->user_key_file,
                               g_file_get_path (desktop_file->user_file),
                               KEY_FILE_FLAGS, NULL);

    return desktop_file;
}

void
pins_desktop_file_save (PinsDesktopFile *self, GError **error)
{
    g_key_file_save_to_file (self->user_key_file,
                             g_file_get_path (self->user_file), error);
}

static void
pins_desktop_file_dispose (GObject *object)
{
    PinsDesktopFile *self = (PinsDesktopFile *)object;

    g_clear_object (&self->user_file);
    g_clear_object (&self->system_key_file);
    g_clear_object (&self->user_key_file);

    G_OBJECT_CLASS (pins_desktop_file_parent_class)->dispose (object);
}

static void
pins_desktop_file_class_init (PinsDesktopFileClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);

    object_class->dispose = pins_desktop_file_dispose;
}

static void
pins_desktop_file_init (PinsDesktopFile *self)
{
}

gboolean
pins_desktop_file_get_boolean (PinsDesktopFile *self, const gchar *key,
                               GError **error)
{
    gboolean value;
    GError *err = NULL;

    value = g_key_file_get_boolean (self->user_key_file,
                                    G_KEY_FILE_DESKTOP_GROUP, key, &err);
    if (g_error_matches (err, G_KEY_FILE_ERROR,
                         G_KEY_FILE_ERROR_INVALID_VALUE))
        {
            return TRUE;
        }
    else if (err != NULL)
        {
            err = NULL;

            value = g_key_file_get_boolean (
                self->system_key_file, G_KEY_FILE_DESKTOP_GROUP, key, &err);
            if (err != NULL)
                {
                    g_propagate_error (error, err);
                    return FALSE;
                }
        }

    return value;
}

gchar *
pins_desktop_file_get_string (PinsDesktopFile *self, const gchar *key,
                              GError **error)
{
    gchar *value;
    GError *err = NULL;

    value = g_key_file_get_string (self->user_key_file,
                                   G_KEY_FILE_DESKTOP_GROUP, key, &err);
    if (err != NULL)
        {
            err = NULL;

            value = g_key_file_get_string (
                self->system_key_file, G_KEY_FILE_DESKTOP_GROUP, key, &err);
            if (err != NULL)
                {
                    g_propagate_error (error, err);
                    return "";
                }
        }

    return value;
}

gchar *
pins_desktop_file_get_locale_string (PinsDesktopFile *self, const gchar *key,
                                     const gchar *locale, GError **error)
{
    gchar *value;
    GError *err = NULL;

    value = g_key_file_get_locale_string (
        self->user_key_file, G_KEY_FILE_DESKTOP_GROUP, key, locale, &err);
    if (err != NULL)
        {
            err = NULL;

            value = g_key_file_get_locale_string (self->system_key_file,
                                                  G_KEY_FILE_DESKTOP_GROUP,
                                                  key, locale, &err);
            if (err != NULL)
                {
                    g_propagate_error (error, err);
                    return "";
                }
        }
    return value;
}

void
pins_desktop_file_set_boolean (PinsDesktopFile *self, const gchar *key,
                               const gboolean value)
{
    g_key_file_set_boolean (self->user_key_file, G_KEY_FILE_DESKTOP_GROUP, key,
                            value);
}

void
pins_desktop_file_set_string (PinsDesktopFile *self, const gchar *key,
                              const gchar *value)
{
    g_key_file_set_string (self->user_key_file, G_KEY_FILE_DESKTOP_GROUP, key,
                           value);
}

void
pins_desktop_file_set_locale_string (PinsDesktopFile *self, const gchar *key,
                                     gchar *value, const gchar *locale)
{
    g_key_file_set_locale_string (
        self->user_key_file, G_KEY_FILE_DESKTOP_GROUP, key, locale, value);
}

void
pins_desktop_file_reset_key (PinsDesktopFile *self, const gchar *key)
{
    g_key_file_remove_key (self->user_key_file, G_KEY_FILE_DESKTOP_GROUP, key,
                           NULL);
}

gboolean
pins_desktop_file_is_key_resettable (PinsDesktopFile *self, const gchar *key)
{
    return g_key_file_has_key (self->user_key_file, G_KEY_FILE_DESKTOP_GROUP,
                               key, NULL);
}
