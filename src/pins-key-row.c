/* pins-key-row.c
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

#include "pins-key-row.h"

struct _PinsKeyRow
{
    AdwEntryRow parent_instance;
};

G_DEFINE_TYPE (PinsKeyRow, pins_key_row, ADW_TYPE_ENTRY_ROW)

PinsKeyRow *
pins_key_row_new (void)
{
    return g_object_new (PINS_TYPE_KEY_ROW, NULL);
}

void
pins_key_row_set_key (PinsKeyRow *self, PinsDesktopFile *desktop_file,
                      gchar *key)
{
    /// TODO: Implement
    adw_preferences_row_set_title (ADW_PREFERENCES_ROW (self), key);
}

static void
pins_key_row_dispose (GObject *object)
{
    G_OBJECT_CLASS (pins_key_row_parent_class)->dispose (object);
}

static void
pins_key_row_class_init (PinsKeyRowClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);

    object_class->dispose = pins_key_row_dispose;
}

static void
pins_key_row_init (PinsKeyRow *self)
{
}
