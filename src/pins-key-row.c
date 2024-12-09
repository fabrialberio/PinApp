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

#include <glib/gi18n.h>

#include "pins-key-row.h"

struct _PinsKeyRow
{
    AdwEntryRow parent_instance;

    PinsDesktopFile *desktop_file;
    gchar *key;

    GtkMenuButton *locale_button;
    GtkPopover *locale_popover;
    GtkListView *locale_list_view;
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
pins_key_row_locale_changed_cb (GtkMenuButton *self, gchar *selected_locale)
{
    AdwButtonContent *button_content
        = ADW_BUTTON_CONTENT (gtk_menu_button_get_child (self));

    if (selected_locale != NULL)
        {
            adw_button_content_set_label (button_content, selected_locale);
        }
    else
        {
            adw_button_content_set_label (button_content, "");
        }
}

void
pins_key_row_locale_menu_item_activated_cb (GtkListView *self, guint position,
                                            gpointer user_data)
{

    g_warning ("Selected row at %d", position);
}

void
pins_key_row_set_key (PinsKeyRow *self, PinsDesktopFile *desktop_file,
                      gchar *key)
{
    gchar *value = pins_desktop_file_get_string (desktop_file, key, NULL);

    self->desktop_file = desktop_file;
    self->key = key;

    adw_preferences_row_set_title (ADW_PREFERENCES_ROW (self), key);
    gtk_editable_set_text (GTK_EDITABLE (self), value);

    /// TODO: Update text when desktop file changes
    g_signal_connect (GTK_EDITABLE (self), "changed",
                      G_CALLBACK (pins_key_row_text_changed_cb), self);
}

void
pins_key_row_set_localized_key (PinsKeyRow *self,
                                PinsDesktopFile *desktop_file, gchar *key)

{
    GStrvBuilder *locales_strv_builder = g_strv_builder_new ();
    GtkSingleSelection *selection_model;

    pins_key_row_set_key (self, desktop_file, key);

    g_strv_builder_add (locales_strv_builder, _ ("( Unlocalized )"));
    g_strv_builder_addv (
        locales_strv_builder,
        (const char **)pins_desktop_file_get_locales (desktop_file));

    selection_model
        = gtk_single_selection_new (G_LIST_MODEL (gtk_string_list_new (
            (const char *const *)g_strv_builder_end (locales_strv_builder))));

    gtk_list_view_set_model (self->locale_list_view,
                             GTK_SELECTION_MODEL (selection_model));
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
    gtk_widget_class_bind_template_child (widget_class, PinsKeyRow,
                                          locale_button);
    gtk_widget_class_bind_template_child (widget_class, PinsKeyRow,
                                          locale_popover);
    gtk_widget_class_bind_template_child (widget_class, PinsKeyRow,
                                          locale_list_view);
}

void
pins_key_row_locale_menu_item_setup_cb (GtkSignalListItemFactory *self,
                                        GtkListItem *item, gpointer user_data)
{
    GtkBuilder *builder = gtk_builder_new_from_resource (
        "/io/github/fabrialberio/pinapp/pins-key-row-locale-menu-item.ui");
    GtkBox *row
        = GTK_BOX (gtk_builder_get_object (builder, "locale_menu_item"));

    gtk_list_item_set_child (item, GTK_WIDGET (row));
}

void
pins_key_row_locale_menu_item_bind_cb (GtkSignalListItemFactory *self,
                                       GtkListItem *item, gpointer user_data)
{
    GtkWidget *row = gtk_list_item_get_child (item);
    GtkLabel *label = GTK_LABEL (gtk_widget_get_first_child (row));
    GtkImage *icon = GTK_IMAGE (gtk_widget_get_last_child (row));
    gchar *locale = (gchar *)gtk_string_object_get_string (
        gtk_list_item_get_item (item));

    gtk_label_set_label (label, locale);

    /// TODO: Update check icon visibility
    gtk_widget_set_visible (GTK_WIDGET (icon), FALSE);
}

static void
pins_key_row_init (PinsKeyRow *self)
{
    GtkListItemFactory *factory = gtk_signal_list_item_factory_new ();

    gtk_widget_init_template (GTK_WIDGET (self));

    g_signal_connect (factory, "setup",
                      G_CALLBACK (pins_key_row_locale_menu_item_setup_cb),
                      NULL);
    g_signal_connect (factory, "bind",
                      G_CALLBACK (pins_key_row_locale_menu_item_bind_cb),
                      NULL);

    gtk_list_view_set_factory (self->locale_list_view, factory);

    g_signal_connect (self->locale_list_view, "activate",
                      G_CALLBACK (pins_key_row_locale_menu_item_activated_cb),
                      NULL);
}
