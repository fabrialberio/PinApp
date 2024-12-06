/* pins-app-view.h
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

#include "pins-app-iterator.h"
#include "pins-app-list.h"

#include <adwaita.h>

G_BEGIN_DECLS

#define PINS_TYPE_APP_VIEW (pins_app_view_get_type ())

G_DECLARE_FINAL_TYPE (PinsAppView, pins_app_view, PINS, APP_VIEW, AdwBin)

void pins_app_view_set_app_iterator (PinsAppView *self,
                                     PinsAppIterator *app_iterator);
void pins_app_view_set_app_list (PinsAppView *self, PinsAppList *app_list);
// void pins_app_view_set_app_grid (PinsAppView *self, PinsAppGrid *app_grid);
void pins_app_view_set_search_entry (PinsAppView *self,
                                     GtkSearchEntry *search_entry);

G_END_DECLS
