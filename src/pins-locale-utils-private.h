/* pins-locale-utils-private.h
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

#include <gtk/gtk.h>

G_BEGIN_DECLS

typedef struct
{
    gchar *key;
    gchar *locale;
} PinsSplitKey;

PinsSplitKey _pins_split_key_locale (gchar *localized_key);
gchar *_pins_join_key_locale (gchar *key, gchar *locale);
gchar **_pins_locales_from_keys (gchar **keys);
gboolean _pins_key_has_locales (gchar **all_keys, gchar *key);
void _gtk_string_list_remove_string (GtkStringList *list, gchar *string);

G_END_DECLS
