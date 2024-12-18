/* pins-file-view.c
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

#include "pins-file-view.h"

#include "pins-app-icon.h"
#include "pins-key-row.h"
#include "pins-locale-utils-private.h"

struct _PinsFileView
{
    AdwBin parent_instance;

    PinsDesktopFile *desktop_file;

    AdwHeaderBar *header_bar;
    AdwWindowTitle *window_title;
    GtkScrolledWindow *scrolled_window;
    PinsAppIcon *icon;
    PinsKeyRow *name_row;
    PinsKeyRow *comment_row;
    GtkListBox *keys_listbox;
    GtkButton *remove_button;
    AdwBreakpoint *breakpoint;
};

G_DEFINE_TYPE (PinsFileView, pins_file_view, ADW_TYPE_BREAKPOINT_BIN);

void
pins_file_view_setup_row (PinsKeyRow *row, PinsDesktopFile *desktop_file,
                          gchar *key, gchar **all_keys, gchar **all_locales)
{
    gchar **locales = { NULL };

    if (_pins_key_has_locales (all_keys, key))
        locales = all_locales;

    pins_key_row_set_key (row, desktop_file, key, locales);
}

void
pins_file_view_update_title (PinsFileView *self)
{
    adw_window_title_set_title (
        self->window_title,
        pins_desktop_file_get_string (self->desktop_file,
                                      G_KEY_FILE_DESKTOP_KEY_NAME, NULL));
}

void
pins_file_view_key_set_cb (PinsDesktopFile *desktop_file, gchar *key,
                           PinsFileView *self)
{
    g_assert (PINS_IS_FILE_VIEW (self));

    if (g_strcmp0 (key, G_KEY_FILE_DESKTOP_KEY_NAME) == 0)
        {
            pins_file_view_update_title (self);
        }
}

void
pins_file_view_update_title_visible_cb (GtkAdjustment *adjustment,
                                        PinsFileView *self)
{
    g_assert (PINS_IS_FILE_VIEW (self));

    adw_header_bar_set_show_title (self->header_bar,
                                   gtk_adjustment_get_value (adjustment) > 0);
}

void
pins_file_view_setup_keys_listbox (PinsFileView *self)
{
    gchar **keys = pins_desktop_file_get_keys (self->desktop_file);
    gchar **locales = _pins_locales_from_keys (keys);
    gchar **added_keys = g_malloc0_n (g_strv_length (keys), sizeof (gchar *));
    gsize n_added_keys = 0;

    gtk_list_box_remove_all (self->keys_listbox);

    pins_file_view_setup_row (self->name_row, self->desktop_file,
                              G_KEY_FILE_DESKTOP_KEY_NAME, keys, locales);
    pins_file_view_setup_row (self->comment_row, self->desktop_file,
                              G_KEY_FILE_DESKTOP_KEY_COMMENT, keys, locales);

    added_keys[0] = G_KEY_FILE_DESKTOP_KEY_NAME;
    added_keys[1] = G_KEY_FILE_DESKTOP_KEY_COMMENT;
    n_added_keys = 2;

    for (int i = 0; keys[i] != NULL; i++)
        {
            gchar *current_key = _pins_split_key_locale (keys[i]).key;
            PinsKeyRow *row;

            if (g_strv_contains ((const gchar *const *)added_keys,
                                 current_key))
                {
                    continue;
                }

            row = pins_key_row_new ();
            pins_file_view_setup_row (row, self->desktop_file, current_key,
                                      keys, locales);

            added_keys[n_added_keys] = current_key;
            n_added_keys++;

            gtk_list_box_append (self->keys_listbox, GTK_WIDGET (row));
        }

    g_strfreev (keys);
    g_strfreev (locales);
    g_free (added_keys); /// TODO: Using g_strfreev results in free error
}

void
pins_file_view_set_desktop_file (PinsFileView *self,
                                 PinsDesktopFile *desktop_file)
{
    self->desktop_file = desktop_file;

    pins_file_view_update_title (self);
    g_signal_connect_object (self->desktop_file, "key-set",
                             G_CALLBACK (pins_file_view_key_set_cb), self, 0);
    g_signal_connect_object (
        gtk_scrolled_window_get_vadjustment (self->scrolled_window),
        "value-changed", G_CALLBACK (pins_file_view_update_title_visible_cb),
        self, 0);

    pins_app_icon_set_desktop_file (self->icon, desktop_file);

    gtk_widget_set_visible (
        GTK_WIDGET (self->remove_button),
        pins_desktop_file_is_user_only (self->desktop_file));

    pins_file_view_setup_keys_listbox (self);
}

PinsDesktopFile *
pins_file_view_get_desktop_file (PinsFileView *self)
{
    return self->desktop_file;
}

static void
pins_file_view_dispose (GObject *object)
{
    gtk_widget_dispose_template (GTK_WIDGET (object), PINS_TYPE_FILE_VIEW);

    G_OBJECT_CLASS (pins_file_view_parent_class)->dispose (object);
}

static void
pins_file_view_class_init (PinsFileViewClass *klass)
{
    GObjectClass *object_class = G_OBJECT_CLASS (klass);
    GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

    object_class->dispose = pins_file_view_dispose;

    gtk_widget_class_set_template_from_resource (
        widget_class, "/io/github/fabrialberio/pinapp/pins-file-view.ui");
    g_type_ensure (PINS_TYPE_APP_ICON);
    g_type_ensure (PINS_TYPE_KEY_ROW);

    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          header_bar);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          window_title);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          scrolled_window);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView, icon);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          name_row);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          comment_row);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          keys_listbox);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          remove_button);
    gtk_widget_class_bind_template_child (widget_class, PinsFileView,
                                          breakpoint);
}

void
pins_file_view_remove_button_clicked_cb (PinsFileView *self)
{
    pins_desktop_file_remove (self->desktop_file);
}

void
breakpoint_apply_cb (PinsFileView *self)
{
    gtk_widget_remove_css_class (GTK_WIDGET (self->name_row), "title-1-row");
    gtk_widget_add_css_class (GTK_WIDGET (self->name_row), "title-2-row");
}

void
breakpoint_unapply_cb (PinsFileView *self)
{
    gtk_widget_remove_css_class (GTK_WIDGET (self->name_row), "title-2-row");
    gtk_widget_add_css_class (GTK_WIDGET (self->name_row), "title-1-row");
}

static void
pins_file_view_init (PinsFileView *self)
{
    gtk_widget_init_template (GTK_WIDGET (self));

    g_signal_connect_object (
        self->remove_button, "clicked",
        G_CALLBACK (pins_file_view_remove_button_clicked_cb), self,
        G_CONNECT_SWAPPED);

    g_signal_connect_object (self->breakpoint, "apply",
                             G_CALLBACK (breakpoint_apply_cb), self,
                             G_CONNECT_SWAPPED);
    g_signal_connect_object (self->breakpoint, "unapply",
                             G_CALLBACK (breakpoint_unapply_cb), self,
                             G_CONNECT_SWAPPED);
}
