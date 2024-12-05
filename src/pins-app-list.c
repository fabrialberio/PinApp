/* pins-app-list.c
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

#include "pins-app-list.h"

#include "pins-app-row.h"

struct _PinsAppList
{
    AdwBin parent_instance;

    GtkListView *list_view;
};

G_DEFINE_TYPE (PinsAppList, pins_app_list, ADW_TYPE_BIN);

void
pins_app_list_item_setup_cb (GtkSignalListItemFactory *self, GtkListItem *item,
                             gpointer user_data)

{
    PinsAppRow *row = pins_app_row_new ();

    gtk_list_item_set_child (item, GTK_WIDGET (row));
}

void
pins_app_list_item_bind_cb (GtkSignalListItemFactory *self, GtkListItem *item,
                            gpointer user_data)
{
    PinsDesktopFile *desktop_file = gtk_list_item_get_item (item);
    PinsAppRow *row = PINS_APP_ROW (gtk_list_item_get_child (item));

    g_assert (PINS_IS_DESKTOP_FILE (desktop_file));

    pins_app_row_set_desktop_file (row, desktop_file);
}

void
pins_app_list_item_unbind_cb (GtkSignalListItemFactory *self,
                              GtkListItem *item, gpointer user_data)
{
}

void
pins_app_list_item_teardown_cb (GtkSignalListItemFactory *self,
                                GtkListItem *item, gpointer user_data)
{
    PinsAppRow *row = PINS_APP_ROW (gtk_list_item_get_child (item));

    g_clear_object (&row);
}

void
pins_app_list_item_activated_cb (GtkListView *self, guint position,
                                 gpointer user_data)
{
    g_warning ("Not implemented");
}

void
pins_app_list_set_app_iterator (PinsAppList *self, GListModel *app_iterator)
{
    GtkNoSelection *model = gtk_no_selection_new (app_iterator);
    GtkListItemFactory *factory = gtk_signal_list_item_factory_new ();

    factory = gtk_signal_list_item_factory_new ();
    g_signal_connect_object (
        factory, "setup", G_CALLBACK (pins_app_list_item_setup_cb), NULL, 0);
    g_signal_connect_object (factory, "bind",
                             G_CALLBACK (pins_app_list_item_bind_cb), NULL, 0);
    g_signal_connect_object (
        factory, "unbind", G_CALLBACK (pins_app_list_item_unbind_cb), NULL, 0);
    g_signal_connect_object (factory, "teardown",
                             G_CALLBACK (pins_app_list_item_teardown_cb), NULL,
                             0);

    gtk_list_view_set_model (self->list_view, GTK_SELECTION_MODEL (model));
    gtk_list_view_set_factory (self->list_view, factory);
    g_signal_connect_object (self->list_view, "activate",
                             G_CALLBACK (pins_app_list_item_activated_cb),
                             NULL, 0);
}

static void
pins_app_list_dispose (GObject *object)
{
    PinsAppList *self = PINS_APP_LIST (object);

    gtk_widget_dispose_template (GTK_WIDGET (object), PINS_TYPE_APP_LIST);

    g_clear_object (&self->list_view);

    G_OBJECT_CLASS (pins_app_list_parent_class)->dispose (object);
}

static void
pins_app_list_class_init (PinsAppListClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);
    GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

    object_class->dispose = pins_app_list_dispose;

    // HACK: Best way i found apply "boxed-list" style class to `ListView`
    gtk_widget_class_set_css_name (
        GTK_WIDGET_CLASS (
            GTK_LIST_VIEW_GET_CLASS (g_object_new (GTK_TYPE_LIST_VIEW, NULL))),
        "list");
    g_type_ensure (PINS_TYPE_APP_ROW);

    gtk_widget_class_set_template_from_resource (
        widget_class, "/io/github/fabrialberio/pinapp/pins-app-list.ui");
    gtk_widget_class_bind_template_child (widget_class, PinsAppList,
                                          list_view);
}

static void
pins_app_list_init (PinsAppList *self)
{
    gtk_widget_init_template (GTK_WIDGET (self));
}
