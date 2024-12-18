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
#include "pins-locale-utils-private.h"

#define DEFAULT_FILENAME "pinned-app"
#define KEY_FILE_FLAGS G_KEY_FILE_KEEP_COMMENTS | G_KEY_FILE_KEEP_TRANSLATIONS

struct _PinsDesktopFile
{
    GObject parent_instance;

    GFile *user_file;
    GFile *system_file;
    GKeyFile *key_file;
    GKeyFile *backup_key_file;
    gchar *saved_data;
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
    KEY_REMOVED,
    FILE_REMOVED,
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
    desktop_file->key_file = g_key_file_new ();
    desktop_file->backup_key_file = g_key_file_new ();

    file_is_user_file = g_file_equal (
        g_file_get_parent (file), g_file_new_for_path (pins_user_app_path ()));

    if (file_is_user_file)
        {
            desktop_file->user_file = file;
            desktop_file->system_file = NULL;

            g_key_file_load_from_file (desktop_file->key_file,
                                       g_file_get_path (file), KEY_FILE_FLAGS,
                                       NULL);
        }
    else
        {
            desktop_file->user_file = g_file_new_for_path (g_strjoin (
                "/", pins_user_app_path (), g_file_get_basename (file), NULL));
            desktop_file->system_file = file;

            if (g_file_query_exists (desktop_file->user_file, NULL))
                {

                    g_key_file_load_from_file (
                        desktop_file->key_file,
                        g_file_get_path (desktop_file->user_file),
                        KEY_FILE_FLAGS, NULL);
                }
            else
                {
                    g_key_file_load_from_file (desktop_file->key_file,
                                               g_file_get_path (file),
                                               KEY_FILE_FLAGS, NULL);
                }

            g_key_file_load_from_file (desktop_file->backup_key_file,
                                       g_file_get_path (file), KEY_FILE_FLAGS,
                                       NULL);
        }

    desktop_file->saved_data
        = g_key_file_to_data (desktop_file->key_file, NULL, NULL);

    return desktop_file;
}

gboolean
pins_desktop_file_is_user_only (PinsDesktopFile *self)
{
    return self->system_file == NULL;
}

/*
 * Returns `TRUE` if the file has been changed since the last save.
 */
gboolean
pins_desktop_file_is_edited (PinsDesktopFile *self)
{
    return g_strcmp0 (g_key_file_to_data (self->key_file, NULL, NULL),
                      self->saved_data)
           != 0;
}

void
pins_desktop_file_remove (PinsDesktopFile *self)
{
    g_file_delete (self->user_file, NULL, NULL);

    g_signal_emit (self, signals[FILE_REMOVED], 0);
}

void
pins_desktop_file_save (PinsDesktopFile *self, GError **error)
{
    if (!pins_desktop_file_is_edited (self))
        return;

    g_warning ("Saving desktop file `%s`", g_file_get_path (self->user_file));

    self->saved_data = g_key_file_to_data (self->key_file, NULL, NULL);

    if (self->system_file != NULL
        && g_strcmp0 (self->saved_data,
                      g_key_file_to_data (self->backup_key_file, NULL, NULL))
               == 0)
        {
            g_file_delete (self->user_file, NULL, NULL);
        }

    g_key_file_save_to_file (self->key_file, g_file_get_path (self->user_file),
                             error);
}

gchar **
pins_desktop_file_get_keys (PinsDesktopFile *self)
{
    g_assert (PINS_IS_DESKTOP_FILE (self));

    return g_key_file_get_keys (self->key_file, G_KEY_FILE_DESKTOP_GROUP, NULL,
                                NULL);
}

gchar **
pins_desktop_file_get_locales (PinsDesktopFile *self)
{
    return _pins_locales_from_keys (pins_desktop_file_get_keys (self));
}

gchar *
pins_desktop_file_get_search_string (PinsDesktopFile *self)
{
    return self->saved_data;
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

    g_object_class_install_properties (object_class, N_PROPS, properties);

    signals[KEY_SET] = g_signal_new ("key-set", G_TYPE_FROM_CLASS (klass),
                                     G_SIGNAL_RUN_FIRST, 0, NULL, NULL, NULL,
                                     G_TYPE_NONE, 1, G_TYPE_STRING);

    signals[KEY_REMOVED] = g_signal_new (
        "key-removed", G_TYPE_FROM_CLASS (klass), G_SIGNAL_RUN_FIRST, 0, NULL,
        NULL, NULL, G_TYPE_NONE, 1, G_TYPE_STRING);

    signals[FILE_REMOVED] = g_signal_new (
        "file-removed", G_TYPE_FROM_CLASS (klass), G_SIGNAL_RUN_LAST, 0, NULL,
        NULL, NULL, G_TYPE_NONE, 0);
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

    value = g_key_file_get_boolean (self->key_file, G_KEY_FILE_DESKTOP_GROUP,
                                    key, &err);
    if (g_error_matches (err, G_KEY_FILE_ERROR,
                         G_KEY_FILE_ERROR_INVALID_VALUE))
        {
            return TRUE;
        }
    else
        {
            g_propagate_error (error, err);
            return FALSE;
        }

    return value;
}

gchar *
pins_desktop_file_get_string (PinsDesktopFile *self, const gchar *key,
                              GError **error)
{
    gchar *value;
    GError *err = NULL;

    value = g_key_file_get_string (self->key_file, G_KEY_FILE_DESKTOP_GROUP,
                                   key, &err);
    if (err != NULL)
        {
            g_propagate_error (error, err);
            return "";
        }

    return value;
}

void
pins_desktop_file_set_boolean (PinsDesktopFile *self, const gchar *key,
                               const gboolean value)
{
    g_key_file_set_boolean (self->key_file, G_KEY_FILE_DESKTOP_GROUP, key,
                            value);

    g_signal_emit (self, signals[KEY_SET], 0, key);
}

void
pins_desktop_file_set_string (PinsDesktopFile *self, const gchar *key,
                              const gchar *value)
{
    g_key_file_set_string (self->key_file, G_KEY_FILE_DESKTOP_GROUP, key,
                           value);

    g_signal_emit (self, signals[KEY_SET], 0, key);
}

gchar *
pins_desktop_file_get_locale_for_key (PinsDesktopFile *self, const gchar *key)
{
    gchar *locale;

    locale = g_key_file_get_locale_for_key (
        self->key_file, G_KEY_FILE_DESKTOP_GROUP, key, NULL);

    if (locale != NULL)
        return locale;

    if (self->system_file == NULL)
        return NULL;

    return g_key_file_get_locale_for_key (self->backup_key_file,
                                          G_KEY_FILE_DESKTOP_GROUP, key, NULL);
}

gboolean
pins_desktop_file_has_backup_for_key (PinsDesktopFile *self, const gchar *key)
{
    if (self->system_file == NULL)
        return FALSE;

    return g_key_file_has_key (self->backup_key_file, G_KEY_FILE_DESKTOP_GROUP,
                               key, NULL);
}

gboolean
pins_desktop_file_has_key (PinsDesktopFile *self, const gchar *key)
{
    return g_key_file_has_key (self->key_file, G_KEY_FILE_DESKTOP_GROUP, key,
                               NULL)
           || pins_desktop_file_has_backup_for_key (self, key);
}

gboolean
pins_desktop_file_is_key_edited (PinsDesktopFile *self, const gchar *key)
{
    if (self->system_file == NULL)
        return TRUE;

    return g_strcmp0 (
               g_key_file_get_string (self->key_file, G_KEY_FILE_DESKTOP_GROUP,
                                      key, NULL),
               g_key_file_get_string (self->backup_key_file,
                                      G_KEY_FILE_DESKTOP_GROUP, key, NULL))
           != 0;
}

void
pins_desktop_file_reset_key (PinsDesktopFile *self, const gchar *key)
{
    if (pins_desktop_file_has_backup_for_key (self, key))
        {
            g_key_file_set_string (
                self->key_file, G_KEY_FILE_DESKTOP_GROUP, key,
                g_key_file_get_string (self->backup_key_file,
                                       G_KEY_FILE_DESKTOP_GROUP, key, NULL));
        }
    else
        {
            g_key_file_remove_key (self->key_file, G_KEY_FILE_DESKTOP_GROUP,
                                   key, NULL);

            g_signal_emit (self, signals[KEY_REMOVED], 0, key);
        }
}
