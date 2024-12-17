/* pins-desktop-file.h
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

#include <gio/gio.h>

G_BEGIN_DECLS

#define PINS_TYPE_DESKTOP_FILE (pins_desktop_file_get_type ())

G_DECLARE_FINAL_TYPE (PinsDesktopFile, pins_desktop_file, PINS, DESKTOP_FILE,
                      GObject);

PinsDesktopFile *pins_desktop_file_new_from_file (GFile *file, GError **error);
gboolean pins_desktop_file_is_user_only (PinsDesktopFile *self);
void pins_desktop_file_save (PinsDesktopFile *self, GError **error);
void pins_desktop_file_remove (PinsDesktopFile *self);

gchar **pins_desktop_file_get_keys (PinsDesktopFile *self);
gchar **pins_desktop_file_get_locales (PinsDesktopFile *self);

gboolean pins_desktop_file_get_boolean (PinsDesktopFile *self,
                                        const gchar *key, GError **error);
gchar *pins_desktop_file_get_string (PinsDesktopFile *self, const gchar *key,
                                     GError **error);
void pins_desktop_file_set_boolean (PinsDesktopFile *self, const gchar *key,
                                    const gboolean value);
void pins_desktop_file_set_string (PinsDesktopFile *self, const gchar *key,
                                   const gchar *value);

gboolean pins_desktop_file_has_backup_for_key (PinsDesktopFile *self,
                                               const gchar *key);
gboolean pins_desktop_file_has_key (PinsDesktopFile *self, const gchar *key);
gboolean pins_desktop_file_is_key_edited (PinsDesktopFile *self,
                                          const gchar *key);
void pins_desktop_file_reset_key (PinsDesktopFile *self, const gchar *key);

G_END_DECLS
