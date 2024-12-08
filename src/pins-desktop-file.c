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
    gboolean is_user_only;
};

G_DEFINE_TYPE (PinsDesktopFile, pins_desktop_file, G_TYPE_OBJECT);

enum
{
    PROP_0,
    PROP_SEARCH_STRING,
    N_PROPS,
};

enum
{
    KEY_SET,
    N_SIGNALS,
};

static GParamSpec *properties[N_PROPS];
static guint signals[N_SIGNALS];

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

    desktop_file = g_object_new (PINS_TYPE_DESKTOP_FILE, NULL);
    desktop_file->user_key_file = g_key_file_new ();
    desktop_file->system_key_file = g_key_file_new ();

    file_is_user_file = g_file_equal (
        g_file_get_parent (file), g_file_new_for_path (pins_user_app_path ()));

    if (file_is_user_file)
        {
            desktop_file->user_file = file;
            desktop_file->is_user_only = TRUE;
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

            desktop_file->is_user_only = FALSE;
        }

    g_key_file_load_from_file (desktop_file->user_key_file,
                               g_file_get_path (desktop_file->user_file),
                               KEY_FILE_FLAGS, NULL);

    return desktop_file;
}

void
pins_desktop_file_save (PinsDesktopFile *self, GError **error)
{
    g_warning ("Saving desktop file `%s`",
               g_file_get_basename (self->user_file));

    g_key_file_save_to_file (self->user_key_file,
                             g_file_get_path (self->user_file), error);
}

gchar **
pins_desktop_file_get_keys (PinsDesktopFile *self)
{
    GStrvBuilder *strv_builder = g_strv_builder_new ();
    GStrv user_keys, system_keys;
    gsize n_user_keys, n_system_keys;

    g_assert (PINS_IS_DESKTOP_FILE (self));

    user_keys = g_key_file_get_keys (
        self->user_key_file, G_KEY_FILE_DESKTOP_GROUP, &n_user_keys, NULL);

    g_strv_builder_addv (strv_builder, (const gchar **)user_keys);

    if (!self->is_user_only)
        {
            system_keys = g_key_file_get_keys (self->system_key_file,
                                               G_KEY_FILE_DESKTOP_GROUP,
                                               &n_system_keys, NULL);

            for (int i = 0; i < n_system_keys; i++)
                {
                    if (!g_strv_contains ((const gchar *const *)user_keys,
                                          system_keys[i]))
                        {
                            g_strv_builder_add (strv_builder, system_keys[i]);
                        }
                }
        }

    return g_strv_builder_end (strv_builder);
}

gchar *
pins_desktop_file_get_search_string (PinsDesktopFile *self)
{
    gchar *user_data, *system_data;
    gsize user_lenght, system_lenght;

    user_data = g_key_file_to_data (self->user_key_file, &user_lenght, NULL);

    if (self->system_key_file == NULL)
        {
            return user_data;
        }

    system_data
        = g_key_file_to_data (self->system_key_file, &system_lenght, NULL);

    return g_ascii_strdown (g_strconcat (user_data, system_data, NULL),
                            user_lenght + system_lenght);
}

static void
pins_desktop_file_get_property (GObject *object, guint prop_id, GValue *value,
                                GParamSpec *pspec)
{
    PinsDesktopFile *self = PINS_DESKTOP_FILE (object);

    switch (prop_id)
        {
        case PROP_SEARCH_STRING:
            g_value_set_string (value,
                                pins_desktop_file_get_search_string (self));
            break;
        default:
            G_OBJECT_WARN_INVALID_PROPERTY_ID (object, prop_id, pspec);
        }
}

static void
pins_desktop_file_class_init (PinsDesktopFileClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);

    object_class->get_property = pins_desktop_file_get_property;

    properties[PROP_SEARCH_STRING]
        = g_param_spec_string ("search-string", "Search String",
                               "Data of the file as a searchable string", "",
                               (G_PARAM_READABLE | G_PARAM_STATIC_STRINGS));

    signals[KEY_SET] = g_signal_new ("key-set", G_TYPE_FROM_CLASS (klass),
                                     G_SIGNAL_RUN_FIRST, 0, NULL, NULL, NULL,
                                     G_TYPE_NONE, 1, G_TYPE_STRING);

    g_object_class_install_properties (object_class, N_PROPS, properties);
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

void
pins_desktop_file_set_boolean (PinsDesktopFile *self, const gchar *key,
                               const gboolean value)
{
    g_key_file_set_boolean (self->user_key_file, G_KEY_FILE_DESKTOP_GROUP, key,
                            value);

    g_signal_emit (self, signals[KEY_SET], 0, key);
}

void
pins_desktop_file_set_string (PinsDesktopFile *self, const gchar *key,
                              const gchar *value)
{
    g_key_file_set_string (self->user_key_file, G_KEY_FILE_DESKTOP_GROUP, key,
                           value);

    g_signal_emit (self, signals[KEY_SET], 0, key);
}

gboolean
pins_desktop_file_is_user_only (PinsDesktopFile *self)
{
    return self->is_user_only;
}

gboolean
pins_desktop_file_is_key_resettable (PinsDesktopFile *self, const gchar *key)
{
    return g_key_file_has_key (self->user_key_file, G_KEY_FILE_DESKTOP_GROUP,
                               key, NULL);
}

void
pins_desktop_file_reset_key (PinsDesktopFile *self, const gchar *key)
{
    g_key_file_remove_key (self->user_key_file, G_KEY_FILE_DESKTOP_GROUP, key,
                           NULL);
}
