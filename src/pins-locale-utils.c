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

void
_pins_split_key_clear (PinsSplitKey *split_key)
{
    g_free (split_key->key);
    g_free (split_key->locale);
}

PinsSplitKey
_pins_split_key_locale (const gchar *localized_key)
{
    g_auto (GStrv) split_result = g_strsplit_set (localized_key, "[]", 3);
    PinsSplitKey result = { NULL, NULL };

    result.key = g_strdup (split_result[0]);
    result.locale = g_strdup (split_result[1]);

    g_assert (split_result[0] != NULL);

    return result;
}

gchar *
_pins_join_key_locale (gchar *key, const gchar *locale)
{
    if (locale != NULL)
        return g_strdup_printf ("%s[%s]", _pins_split_key_locale (key).key,
                                locale);
    else
        return key;
}

gchar **
_pins_locales_from_keys (gchar **keys)
{
    GHashTable *unique_locales = g_hash_table_new (g_str_hash, g_str_equal);
    GStrvBuilder *strv_builder = g_strv_builder_new ();

    for (int i = 0; i < g_strv_length (keys); i++)
        {
            PinsSplitKey split = _pins_split_key_locale (keys[i]);
            g_free (split.key);

            if (split.locale != NULL
                && !g_hash_table_contains (unique_locales, split.locale))
                {
                    g_strv_builder_add (strv_builder, split.locale);
                    g_hash_table_add (unique_locales, split.locale);
                }
        }

    g_hash_table_foreach (unique_locales, (GHFunc)g_free, NULL);
    g_hash_table_destroy (unique_locales);
    return g_strv_builder_end (strv_builder);
}

gboolean
_pins_key_has_locales (gchar **all_keys, const gchar *key)
{
    g_auto (PinsSplitKey) split, current;

    split = _pins_split_key_locale (key);

    for (int i = 0; i < g_strv_length (all_keys); i++)
        {
            current = _pins_split_key_locale (all_keys[i]);

            if (!g_strcmp0 (current.key, split.key) && current.locale != NULL)
                return TRUE;
        }

    return FALSE;
}
