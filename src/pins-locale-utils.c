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

PinsSplitKey
_pins_split_key_locale (gchar *localized_key)
{
    gchar **split_result = g_strsplit_set (localized_key, "[]", 3);
    PinsSplitKey result = {
        .key = split_result[0],
        .locale = split_result[1],
    };

    g_assert (split_result[0] != NULL);

    return result;
}

gchar *
_pins_join_key_locale (gchar *key, gchar *locale)
{
    if (locale != NULL)
        {
            return g_strdup_printf ("%s[%s]", _pins_split_key_locale (key).key,
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
    gchar **locales = g_malloc0_n (g_strv_length (keys) + 1, sizeof (gchar *));

    GStrvBuilder *strv_builder = g_strv_builder_new ();

    for (int i = 0, lenght = 0; i < g_strv_length (keys); i++)
        {
            locale = _pins_split_key_locale (keys[i]).locale;

            if (locale != NULL
                && !g_strv_contains ((const gchar *const *)locales, locale))
                {
                    locales[lenght] = locale;
                    lenght++;
                }
        }

    g_strv_builder_addv (strv_builder, (const char **)locales);

    g_free (locale);
    g_free (locales);

    return g_strv_builder_end (strv_builder);
}

gboolean
_pins_key_has_locales (gchar **all_keys, gchar *key)
{
    PinsSplitKey split_key;

    key = _pins_split_key_locale (key).key;

    for (int i = 0; i < g_strv_length (all_keys); i++)
        {
            split_key = _pins_split_key_locale (all_keys[i]);

            if (g_strcmp0 (split_key.key, key) == 0
                && split_key.locale != NULL)
                {
                    return TRUE;
                }
        }

    return FALSE;
}
