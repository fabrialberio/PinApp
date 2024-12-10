/* pins-locale-utils.c
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

#pragma once

#include "pins-locale-utils-private.h"

/**
 * Returns a 2-element string array containing key and locale (NULL if not
 * present).
 */
gchar **
_pins_split_key_locale (gchar *localized_key)
{
    gchar **key_locale = g_strsplit (localized_key, "[", 2);

    g_assert (key_locale[0] != NULL);

    if (key_locale[1] != NULL)
        {
            /// TODO: Does this actually work? (supposed to remove trailing
            /// ']')
            key_locale[1]
                = g_strndup (key_locale[1], strlen (key_locale[1]) - 1);
        }

    return key_locale;
}

gchar *
_pins_join_key_locale (gchar *key, gchar *locale)
{
    if (locale != NULL)
        {
            return g_strdup_printf ("%s[%s]", _pins_split_key_locale (key)[0],
                                    locale);
        }
    else
        {
            return key;
        }
}

gchar **
_pins_locales_from_keys (gchar **keys)
{
    gchar *locale = g_malloc (sizeof (gchar *));
    gchar **locales = g_malloc0_n (g_strv_length (keys), sizeof (gchar *));
    GStrvBuilder *strv_builder = g_strv_builder_new ();

    for (int i = 0, lenght = 0; keys[i] != NULL; i++)
        {
            locale = _pins_split_key_locale (keys[i])[1];

            if (locale != NULL
                && !g_strv_contains ((const gchar *const *)locales, locale))
                {
                    locales[lenght] = locale;
                    lenght++;
                }
        }

    g_strv_builder_addv (strv_builder, (const char **)locales);

    g_free (locale);
    g_strfreev (locales);

    return g_strv_builder_end (strv_builder);
}

gboolean
_pins_key_has_locales (gchar **keys, gchar *key)
{
    gchar **current_key_locale = g_malloc_n (2, sizeof (gchar *));

    key = _pins_split_key_locale (key)[0];

    for (int i = 0; keys[i] != NULL; i++)
        {
            current_key_locale = _pins_split_key_locale (keys[i]);

            if (g_strcmp0 (current_key_locale[0], key) == 0
                && current_key_locale[1] != NULL)
                {
                    g_strfreev (current_key_locale);
                    return TRUE;
                }
        }

    g_strfreev (current_key_locale);
    return FALSE;
}
