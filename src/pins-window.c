/* pins-window.c
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

#include "pins-window.h"

#include "pins-app-iterator.h"
#include "pins-app-view.h"
#include "pins-desktop-file.h"
#include "pins-directories.h"
#include "pins-file-view.h"

struct _PinsWindow
{
    AdwApplicationWindow parent_instance;

    /* Template widgets */
    GtkButton *new_file_button;
    GtkToggleButton *search_button;
    GtkSearchBar *search_bar;
    GtkSearchEntry *search_entry;
    AdwNavigationView *navigation_view;
    PinsAppView *app_view;
    PinsAppView *search_view;
    PinsFileView *file_view;
};

G_DEFINE_FINAL_TYPE (PinsWindow, pins_window, ADW_TYPE_APPLICATION_WINDOW)

enum
{
    PAGE_APPS,
    PAGE_FILE,
    N_PAGES,
};

static gchar *pages[N_PAGES] = {
    "apps-page",
    "file-page",
};

static void
pins_window_dispose (GObject *object)
{
    gtk_widget_dispose_template (GTK_WIDGET (object), PINS_TYPE_WINDOW);

    G_OBJECT_CLASS (pins_window_parent_class)->dispose (object);
}

static void
pins_window_class_init (PinsWindowClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);
    GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

    object_class->dispose = pins_window_dispose;

    gtk_widget_class_set_template_from_resource (
        widget_class, "/io/github/fabrialberio/pinapp/pins-window.ui");
    g_type_ensure (PINS_TYPE_APP_VIEW);
    g_type_ensure (PINS_TYPE_FILE_VIEW);

    gtk_widget_class_bind_template_child (widget_class, PinsWindow,
                                          new_file_button);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow,
                                          search_button);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow,
                                          search_bar);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow,
                                          search_entry);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow,
                                          navigation_view);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow, app_view);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow,
                                          search_view);
    gtk_widget_class_bind_template_child (widget_class, PinsWindow, file_view);
}

void
pins_window_item_activated_cb (GtkListView *self,
                               PinsDesktopFile *desktop_file,
                               PinsWindow *user_data)
{
    g_assert (PINS_IS_WINDOW (user_data));
    g_assert (PINS_IS_DESKTOP_FILE (desktop_file));

    pins_file_view_set_desktop_file (user_data->file_view, desktop_file);

    adw_navigation_view_push_by_tag (user_data->navigation_view,
                                     pages[PAGE_FILE]);
}

static void
pins_window_init (PinsWindow *self)
{
    GtkIconTheme *theme;
    PinsAppIterator *app_iterator;

    gtk_widget_init_template (GTK_WIDGET (self));

    theme = gtk_icon_theme_get_for_display (
        gtk_widget_get_display (GTK_WIDGET (self)));

    // This is noticeably slow
    pins_icon_theme_inject_search_paths (theme);

    gtk_search_bar_connect_entry (self->search_bar,
                                  GTK_EDITABLE (self->search_entry));

    app_iterator = pins_app_iterator_new ();
    pins_app_iterator_set_paths (app_iterator, pins_all_app_paths ());

    pins_app_view_set_app_iterator (self->app_view, app_iterator);
    pins_app_view_set_app_list (self->app_view, pins_app_list_new ());

    pins_app_view_set_app_iterator (self->search_view, app_iterator);
    pins_app_view_set_app_list (self->search_view, pins_app_list_new ());
    pins_app_view_set_search_entry (self->search_view, self->search_entry);

    g_signal_connect (self->app_view, "activate",
                      G_CALLBACK (pins_window_item_activated_cb), self);

    g_signal_connect (self->search_view, "activate",
                      G_CALLBACK (pins_window_item_activated_cb), self);
}
