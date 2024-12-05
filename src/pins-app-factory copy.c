/* pins-app-factory.c
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

#include "pins-app-factory.h"
#include "pins-app-row.h"

void
pins_app_factory_setup_cb (GtkSignalListItemFactory *self, GtkListItem *item,
                           gpointer user_data)

{
    PinsAppRow *row = pins_app_row_new ();

    gtk_list_item_set_child (item, GTK_WIDGET (row));
}

void
pins_app_factory_bind_cb (GtkSignalListItemFactory *self, GtkListItem *item,
                          gpointer user_data)
{
    PinsDesktopFile *desktop_file = gtk_list_item_get_item (item);
    PinsAppRow *row = PINS_APP_ROW (gtk_list_item_get_child (item));

    g_assert (PINS_IS_DESKTOP_FILE (desktop_file));

    pins_app_row_set_desktop_file (row, desktop_file);
}

void
pins_app_factory_unbind_cb (GtkSignalListItemFactory *self, GtkListItem *item,
                            gpointer user_data)
{
}

void
pins_app_factory_teardown_cb (GtkSignalListItemFactory *self,
                              GtkListItem *item, gpointer user_data)
{
    PinsAppRow *row = PINS_APP_ROW (gtk_list_item_get_child (item));

    g_clear_object (&row);
}

GtkListItemFactory *
pins_app_factory_new (void)
{
    GtkListItemFactory *factory = gtk_signal_list_item_factory_new ();

    g_signal_connect_object (factory, "setup",
                             G_CALLBACK (pins_app_factory_setup_cb), NULL, 0);
    g_signal_connect_object (factory, "bind",
                             G_CALLBACK (pins_app_factory_bind_cb), NULL, 0);
    g_signal_connect_object (factory, "unbind",
                             G_CALLBACK (pins_app_factory_unbind_cb), NULL, 0);
    g_signal_connect_object (factory, "teardown",
                             G_CALLBACK (pins_app_factory_teardown_cb), NULL,
                             0);

    return factory;
}
