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

    PinsDesktopFile *desktop_file;
    gchar *key;
};

G_DEFINE_TYPE (PinsKeyRow, pins_key_row, ADW_TYPE_ENTRY_ROW)

PinsKeyRow *
pins_key_row_new (void)
{
    return g_object_new (PINS_TYPE_KEY_ROW, NULL);
}

void
pins_key_row_text_changed_cb (GtkEditable *self, PinsKeyRow *user_data)
{
    g_assert (PINS_IS_KEY_ROW (user_data));

    pins_desktop_file_set_string (user_data->desktop_file, user_data->key,
                                  gtk_editable_get_text (self));
}

void
pins_key_row_set_key (PinsKeyRow *self, PinsDesktopFile *desktop_file,
                      gchar *key)
{
    self->desktop_file = desktop_file;
    self->key = key;

    gchar *value = pins_desktop_file_get_string (desktop_file, key, NULL);

    adw_preferences_row_set_title (ADW_PREFERENCES_ROW (self), key);
    gtk_editable_set_text (GTK_EDITABLE (self), value);

    /// TODO: Update text when desktop file changes
    g_signal_connect (GTK_EDITABLE (self), "changed",
                      G_CALLBACK (pins_key_row_text_changed_cb), self);
}

static void
pins_key_row_dispose (GObject *object)
{
    gtk_widget_dispose_template (GTK_WIDGET (object), PINS_TYPE_KEY_ROW);

    G_OBJECT_CLASS (pins_key_row_parent_class)->dispose (object);
}

static void
pins_key_row_class_init (PinsKeyRowClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);
    GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

    object_class->dispose = pins_key_row_dispose;

    gtk_widget_class_set_template_from_resource (
        widget_class, "/io/github/fabrialberio/pinapp/pins-key-row.ui");
}

static void
pins_key_row_init (PinsKeyRow *self)
{
    gtk_widget_init_template (GTK_WIDGET (self));
}
