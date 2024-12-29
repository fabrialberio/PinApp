/* pins-app-view.c
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

// Widget that handles:
// - Filtering a model for search
// - Showing loading / placeholder

#include "pins-app-view.h"

#include "pins-app-list.h"
#include "pins-desktop-file.h"

struct _PinsAppView
{
    AdwBin parent_instance;

    GtkStringFilter *string_filter;
    GtkFilterListModel *filter_model;

    GtkButton *new_file_button;
    GtkToggleButton *search_button;
    GtkSearchBar *search_bar;
    GtkSearchEntry *search_entry;
    AdwViewStack *view_stack;
    PinsAppList *app_list;
};

G_DEFINE_TYPE (PinsAppView, pins_app_view, ADW_TYPE_BIN);

enum
{
    ACTIVATE,
    N_SIGNALS
};

enum
{
    PAGE_APPS,
    PAGE_EMPTY,
    PAGE_LOADING,
    N_PAGES,
};

static guint signals[N_SIGNALS];
static gchar *pages[N_PAGES] = {
    "apps",
    "empty",
    "loading",
};

void
app_iterator_loading_cb (PinsAppIterator *app_iterator, gboolean is_loading,
                         PinsAppView *self)
{
    g_assert (PINS_IS_APP_VIEW (self));

    if (is_loading)
        adw_view_stack_set_visible_child_name (self->view_stack,
                                               pages[PAGE_LOADING]);
    else
        adw_view_stack_set_visible_child_name (self->view_stack,
                                               pages[PAGE_APPS]);
}

void
app_iterator_file_created_cb (PinsAppIterator *app_iterator,
                              PinsDesktopFile *desktop_file, PinsAppView *self)
{
    g_signal_emit (self, signals[ACTIVATE], 0, desktop_file);
}

void
pins_app_view_set_app_iterator (PinsAppView *self,
                                PinsAppIterator *app_iterator)
{
    adw_view_stack_set_visible_child_name (self->view_stack,
                                           pages[PAGE_LOADING]);

    self->filter_model = gtk_filter_list_model_new (
        G_LIST_MODEL (app_iterator), GTK_FILTER (self->string_filter));

    pins_app_list_set_model (self->app_list,
                             G_LIST_MODEL (g_object_ref (self->filter_model)));

    g_signal_connect_object (app_iterator, "loading",
                             G_CALLBACK (app_iterator_loading_cb), self, 0);
    g_signal_connect_object (app_iterator, "file-created",
                             G_CALLBACK (app_iterator_file_created_cb), self,
                             0);
}

static void
pins_app_view_dispose (GObject *object)
{
    PinsAppView *self = PINS_APP_VIEW (object);

    g_clear_object (&self->string_filter);
    g_clear_object (&self->filter_model);

    gtk_widget_dispose_template (GTK_WIDGET (object), PINS_TYPE_APP_VIEW);

    G_OBJECT_CLASS (pins_app_view_parent_class)->dispose (object);
}

static void
pins_app_view_class_init (PinsAppViewClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);
    GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

    object_class->dispose = pins_app_view_dispose;

    signals[ACTIVATE] = g_signal_new ("activate", G_TYPE_FROM_CLASS (klass),
                                      G_SIGNAL_RUN_LAST, 0, NULL, NULL, NULL,
                                      G_TYPE_NONE, 1, G_TYPE_OBJECT);

    gtk_widget_class_set_template_from_resource (
        widget_class, "/io/github/fabrialberio/pinapp/pins-app-view.ui");
    g_type_ensure (PINS_TYPE_APP_LIST);

    gtk_widget_class_bind_template_child (widget_class, PinsAppView,
                                          new_file_button);
    gtk_widget_class_bind_template_child (widget_class, PinsAppView,
                                          search_button);
    gtk_widget_class_bind_template_child (widget_class, PinsAppView,
                                          search_bar);
    gtk_widget_class_bind_template_child (widget_class, PinsAppView,
                                          search_entry);
    gtk_widget_class_bind_template_child (widget_class, PinsAppView,
                                          view_stack);
    gtk_widget_class_bind_template_child (widget_class, PinsAppView, app_list);
}

void
pins_app_view_search_changed_cb (GtkSearchEntry *entry, PinsAppView *self)
{
    g_assert (PINS_IS_APP_VIEW (self));

    gtk_string_filter_set_search (
        self->string_filter, gtk_editable_get_text (GTK_EDITABLE (entry)));

    if (g_list_model_get_n_items (G_LIST_MODEL (self->filter_model)) == 0)
        {
            adw_view_stack_set_visible_child_name (self->view_stack,
                                                   pages[PAGE_EMPTY]);
        }
    else
        {
            adw_view_stack_set_visible_child_name (self->view_stack,
                                                   pages[PAGE_APPS]);
        }
}

void
pins_app_view_create_file_cb (PinsAppView *self)
{
    PinsAppIterator *app_iterator = PINS_APP_ITERATOR (
        gtk_filter_list_model_get_model (self->filter_model));

    pins_app_iterator_create_user_file (app_iterator, "pinned-app", NULL);
}

void
pins_app_view_item_activated_cb (GtkListView *self, guint position,
                                 PinsAppView *user_data)
{
    PinsDesktopFile *desktop_file;

    g_assert (PINS_IS_APP_VIEW (user_data));

    desktop_file = g_list_model_get_item (
        G_LIST_MODEL (user_data->filter_model), position);

    g_signal_emit (user_data, signals[ACTIVATE], 0, desktop_file);
}

static void
pins_app_view_init (PinsAppView *self)
{
    gtk_widget_init_template (GTK_WIDGET (self));

    self->string_filter = gtk_string_filter_new (gtk_property_expression_new (
        PINS_TYPE_DESKTOP_FILE, NULL, "search-string"));

    adw_view_stack_set_visible_child_name (self->view_stack,
                                           pages[PAGE_LOADING]);

    gtk_search_bar_connect_entry (self->search_bar,
                                  GTK_EDITABLE (self->search_entry));

    g_signal_connect_object (self->search_entry, "search-changed",
                             G_CALLBACK (pins_app_view_search_changed_cb),
                             self, 0);
    g_signal_connect_object (self->app_list, "activate",
                             G_CALLBACK (pins_app_view_item_activated_cb),
                             self, 0);
    g_signal_connect_object (self->new_file_button, "clicked",
                             G_CALLBACK (pins_app_view_create_file_cb), self,
                             G_CONNECT_SWAPPED);
}
