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

enum
{
    ACTIVATE,
    N_SIGNALS
};

static guint signals[N_SIGNALS];

PinsAppList *
pins_app_list_new (void)
{
    return g_object_new (PINS_TYPE_APP_LIST, NULL);
}

void
pins_app_list_item_activated_cb (GtkListView *self, guint position,
                                 PinsAppList *user_data)
{
    g_assert (PINS_IS_APP_LIST (user_data));

    g_signal_emit (user_data, signals[ACTIVATE], 0, position);
}

void
pins_app_list_set_model (PinsAppList *self, GListModel *model)
{
    GtkNoSelection *selection_model = gtk_no_selection_new (model);

    /// TODO: Causes "g_object_unref: assertion 'G_IS_OBJECT (object)' failed"
    gtk_list_view_set_model (self->list_view,
                             GTK_SELECTION_MODEL (selection_model));

    g_signal_connect_object (self->list_view, "activate",
                             G_CALLBACK (pins_app_list_item_activated_cb),
                             self, 0);
}

static void
pins_app_list_dispose (GObject *object)
{
    gtk_widget_dispose_template (GTK_WIDGET (object), PINS_TYPE_APP_LIST);

    G_OBJECT_CLASS (pins_app_list_parent_class)->dispose (object);
}

static void
pins_app_list_class_init (PinsAppListClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);
    GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

    object_class->dispose = pins_app_list_dispose;

    signals[ACTIVATE] = g_signal_new (
        "activate", G_TYPE_FROM_CLASS (klass), G_SIGNAL_RUN_LAST, 0, NULL,
        NULL, g_cclosure_marshal_VOID__UINT, G_TYPE_NONE, 1, G_TYPE_UINT);

    g_signal_set_va_marshaller (signals[ACTIVATE], G_TYPE_FROM_CLASS (klass),
                                g_cclosure_marshal_VOID__UINTv);

    // HACK: Best way i found apply "boxed-list" style class to `ListView`
    gtk_widget_class_set_css_name (
        GTK_WIDGET_CLASS (
            GTK_LIST_VIEW_GET_CLASS (g_object_new (GTK_TYPE_LIST_VIEW, NULL))),
        "list");

    gtk_widget_class_set_template_from_resource (
        widget_class, "/io/github/fabrialberio/pinapp/pins-app-list.ui");
    gtk_widget_class_bind_template_child (widget_class, PinsAppList,
                                          list_view);
}

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

static void
pins_app_list_init (PinsAppList *self)
{
    GtkListItemFactory *factory = gtk_signal_list_item_factory_new ();

    gtk_widget_init_template (GTK_WIDGET (self));

    g_signal_connect_object (
        factory, "setup", G_CALLBACK (pins_app_list_item_setup_cb), NULL, 0);
    g_signal_connect_object (factory, "bind",
                             G_CALLBACK (pins_app_list_item_bind_cb), NULL, 0);

    gtk_list_view_set_factory (self->list_view, factory);
}
