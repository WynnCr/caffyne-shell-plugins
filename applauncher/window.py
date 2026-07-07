import os
import json
import subprocess
import urllib.parse
import threading
import re
import signal

from fabric.widgets.wayland import WaylandWindow
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.image import Image
from fabric.widgets.centerbox import CenterBox
from snippets import StyleAwareEntry, AnimatedScroll, Icon
from fabric.utils import get_desktop_applications
from windows.launcher import load_usage, get_usage_count
from thefuzz import fuzz
from gi.repository import Gdk, GLib, Gtk

from .utils import try_math, quick_file_search, load_bookmarks, toggle_bookmark, get_app_id
from .commands import BuiltinCommand, BUILTIN_COMMANDS
from .item import AppLauncherItem
from .emoji import EmojiPage

_global_launcher_instance = None
def get_launcher_window():
    global _global_launcher_instance
    if _global_launcher_instance is None:
        _global_launcher_instance = AppLauncherWindow()
    return _global_launcher_instance

class AppLauncherWindow(WaylandWindow):
    def __init__(self):
        super().__init__(
            layer="top",
            anchor="center",
            keyboard_mode="exclusive",
            exclusivity="none",
            style_classes=["applauncher-window"],
        )
        
        self._selected_index = 0
        self._open_windows_cache = []  # initialize cache to avoid AttributeError on first search
        self._all_apps = get_desktop_applications()
        self._item_pool = [AppLauncherItem(self) for _ in range(20)]
        self._pool_idx = 0
        self._last_toggle_time = 0
        
        self.search_entry = StyleAwareEntry(
            placeholder="Search for anything...",
            style_classes=["applauncher-search"],
            on_changed=lambda e, *_: self._search(e.get_text()),
            on_activate=lambda *_: self._activate_selected(),
        )
        self.search_entry.connect("key-press-event", self._on_entry_key_press)
        
        self.results_box = Box(orientation="v", spacing=2)
        
        self.scrolled_window = AnimatedScroll(
            style_classes=["applauncher-scroll"],
            child=self.results_box,
            min_content_size=(650, 300),
            max_content_size=(650, 500),
            h_expand=True,
            v_expand=True,
        )
        
        self._emoji_page = EmojiPage(hide_callback=self.hide_launcher)

        self._emoji_toggle_btn = Button(
            child=Image(icon_name="face-smile-symbolic", icon_size=16),
            style_classes=["header-icon-btn"],
            on_clicked=self._toggle_emoji_view,
        )

        self.header = CenterBox(
            style_classes=["applauncher-header-box"],
            start_children=Box(
                spacing=8,
                children=[
                    Label(label="Apps", style_classes=["header-title"]),
                    Label(label="·", style_classes=["header-dot"]),
                    Label(label=f"{len(self._all_apps)}", style_classes=["header-count"])
                ]
            ),
            end_children=self._emoji_toggle_btn,
        )

        self.search_box = Box(
            style_classes=["search-box-container"],
            spacing=8,
            children=[
                Image(icon_name="system-search-symbolic", icon_size=16, style_classes=["search-icon"]),
                self.search_entry
            ]
        )
        self._launcher_page = Box(
            orientation="v",
            spacing=0,
            children=[self.search_box, self.scrolled_window],
        )
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(150)
        self._stack.add_named(self._launcher_page.get_internal_children()[0]
                              if False else self._launcher_page, "launcher")
        self._stack.add_named(self._emoji_page, "emoji")

        self.main_box = Box(
            orientation="v",
            spacing=0,
            style_classes=["applauncher-container"],
            children=[
                self.header,
                self._stack,
            ]
        )

        self.add(self.main_box)
        self.connect("key-press-event", self._on_key_press)

        self.set_visible(False)
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR1, self._on_sigusr1)
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR2, self._on_sigusr2)

    def _on_sigusr1(self):
        now = GLib.get_monotonic_time() / 1000
        if now - self._last_toggle_time < 300:
            return True
        self._last_toggle_time = now

        if self.get_visible() and self._stack.get_visible_child_name() == "launcher":
            self.hide_launcher()
        else:
            self.show_launcher(page="launcher")
        return True

    def _on_sigusr2(self):
        now = GLib.get_monotonic_time() / 1000
        if now - self._last_toggle_time < 300:
            return True
        self._last_toggle_time = now

        if self.get_visible() and self._stack.get_visible_child_name() == "emoji":
            self.hide_launcher()
        else:
            self.show_launcher(page="emoji")
        return True

    def _toggle_emoji_view(self, *_):
        if self._stack.get_visible_child_name() == "emoji":
            self._stack.set_visible_child_name("launcher")
            self._emoji_toggle_btn.child = Image(
                icon_name="face-smile-symbolic", icon_size=16
            )
            self._emoji_toggle_btn.get_style_context().remove_class("active")
            GLib.idle_add(self.search_entry.grab_focus)
        else:
            self._stack.set_visible_child_name("emoji")
            self._emoji_page.reset()
            self._emoji_toggle_btn.child = Image(
                icon_name="view-grid-symbolic", icon_size=16
            )
            self._emoji_toggle_btn.get_style_context().add_class("active")
            GLib.idle_add(self._emoji_page._entry.grab_focus)

        
    def _clear_results(self):
        for child in self.results_box.get_children():
            self.results_box.remove(child)
            if not isinstance(child, AppLauncherItem):
                child.destroy()
        self._pool_idx = 0

    def _add_item(self, item, is_cmd=False):
        if self._pool_idx < len(self._item_pool):
            widget = self._item_pool[self._pool_idx]
            self._pool_idx += 1
        else:
            widget = AppLauncherItem(self)
            self._item_pool.append(widget)
            
        widget.set_item(item, is_cmd)
        self.results_box.add(widget)
        widget.show()

    def _search(self, query):
        self._selected_index = 0
        self._clear_results()
            
        if not query:
            self._populate_default()
            return
            
        query_lower = query.lower()
            
        if query_lower == "confirm reboot":
            raw_cmd = BuiltinCommand("Yes, Reboot Now", "Restart system", "system-reboot-symbolic", "systemctl reboot")
            self._add_item(raw_cmd, is_cmd=True)
            return
            
        if query_lower == "confirm shutdown":
            raw_cmd = BuiltinCommand("Yes, Shutdown Now", "Power off system", "system-shutdown-symbolic", "systemctl poweroff")
            self._add_item(raw_cmd, is_cmd=True)
            return
            
        if query_lower == "confirm sleep":
            raw_cmd = BuiltinCommand("Yes, Sleep Now", "Suspend system", "system-suspend-symbolic", "systemctl suspend")
            self._add_item(raw_cmd, is_cmd=True)
            return
            
        if query.startswith(">"):
            cmd = query[1:].strip()
            if cmd:
                cmd_line = f"sh -c '{cmd}'"
                raw_cmd = BuiltinCommand(f"Run: {cmd}", "Execute shell command", "utilities-terminal-symbolic", cmd_line)
                self._add_item(raw_cmd, is_cmd=True)
            return

        if query.startswith("?"):
            term = query[1:].strip()
            if term:
                url = f"https://duckduckgo.com/?q={urllib.parse.quote_plus(term)}"
                raw_cmd = BuiltinCommand(f"Search Web: {term}", "Search DuckDuckGo", "web-browser-symbolic", f"xdg-open '{url}'")
                self._add_item(raw_cmd, is_cmd=True)
            return
            
        if query.startswith("!"):
            term = query[1:].strip()
            if term:
                files = quick_file_search(term)
                for f in files:
                    icon = "folder-symbolic" if os.path.isdir(f) else "text-x-generic-symbolic"
                    raw_cmd = BuiltinCommand(os.path.basename(f), f, icon, f"xdg-open '{f}'")
                    self._add_item(raw_cmd, is_cmd=True)
            return
            
        # --- QUICK ACTIONS MODULES ---
        if query_lower.startswith("vol "):
            term = query_lower[4:].strip()
            if term.isdigit() and 0 <= int(term) <= 100:
                raw_cmd = BuiltinCommand(f"Set Volume to {term}%", "System Audio", "audio-volume-high-symbolic", f"wpctl set-volume @DEFAULT_AUDIO_SINK@ {term}%")
            else:
                raw_cmd = BuiltinCommand("Set Volume...", "Type a percentage (0-100)", "audio-volume-high-symbolic", "")
            self._add_item(raw_cmd, is_cmd=True)
            return
                
        if query_lower.startswith("bright "):
            term = query_lower[7:].strip()
            if term.isdigit() and 0 <= int(term) <= 100:
                raw_cmd = BuiltinCommand(f"Set Brightness to {term}%", "Display", "display-brightness-symbolic", f"brightnessctl set {term}%")
            else:
                raw_cmd = BuiltinCommand("Set Brightness...", "Type a percentage (0-100)", "display-brightness-symbolic", "")
            self._add_item(raw_cmd, is_cmd=True)
            return
                
        if query_lower.startswith("kill "):
            term = query[5:].strip()
            if term:
                raw_cmd = BuiltinCommand(f"Kill '{term}'", "Terminate Process", "application-exit-symbolic", f"pkill -f '{term}'")
            else:
                raw_cmd = BuiltinCommand("Kill Process...", "Type a process name", "application-exit-symbolic", "")
            self._add_item(raw_cmd, is_cmd=True)
            return
                

                
        if query_lower.startswith("ssh "):
            term = query[4:].strip()
            if term:
                raw_cmd = BuiltinCommand(f"SSH to {term}", "Remote Connection", "utilities-terminal-symbolic", f"ghostty -e ssh {term}")
            else:
                raw_cmd = BuiltinCommand("SSH Connection...", "Type hostname or IP", "utilities-terminal-symbolic", "")
            self._add_item(raw_cmd, is_cmd=True)
            return
                
        if query_lower.startswith("def "):
            term = query[4:].strip()
            if term:
                url = f"https://en.wiktionary.org/wiki/{urllib.parse.quote_plus(term)}"
                raw_cmd = BuiltinCommand(f"Define: {term}", "Wiktionary", "accessories-dictionary-symbolic", f"xdg-open '{url}'")
            else:
                raw_cmd = BuiltinCommand("Dictionary...", "Type a word to define", "accessories-dictionary-symbolic", "")
            self._add_item(raw_cmd, is_cmd=True)
            return
            
        if query_lower.startswith("yt "):
            term = query[3:].strip()
            if term:
                url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(term)}"
                raw_cmd = BuiltinCommand(f"YouTube: {term}", "Search YouTube", "media-playback-start-symbolic", f"xdg-open '{url}'")
            else:
                raw_cmd = BuiltinCommand("Search YouTube...", "Type a video name", "media-playback-start-symbolic", "")
            self._add_item(raw_cmd, is_cmd=True)
            return
            
        if query_lower.startswith("gh "):
            term = query[3:].strip()
            if term:
                url = f"https://github.com/search?q={urllib.parse.quote_plus(term)}"
                raw_cmd = BuiltinCommand(f"GitHub: {term}", "Search Repositories", "applications-development-symbolic", f"xdg-open '{url}'")
            else:
                raw_cmd = BuiltinCommand("Search GitHub...", "Type a repository or user", "applications-development-symbolic", "")
            self._add_item(raw_cmd, is_cmd=True)
            return
            
        if query_lower.startswith("wiki "):
            term = query[5:].strip()
            if term:
                url = f"https://en.wikipedia.org/wiki/Special:Search?search={urllib.parse.quote_plus(term)}"
                raw_cmd = BuiltinCommand(f"Wikipedia: {term}", "Search Wikipedia", "accessories-dictionary-symbolic", f"xdg-open '{url}'")
            else:
                raw_cmd = BuiltinCommand("Search Wikipedia...", "Type an article name", "accessories-dictionary-symbolic", "")
            self._add_item(raw_cmd, is_cmd=True)
            return
        # ----------------------------
            
        math_res = try_math(query)
        if math_res is not None:
            raw_cmd = BuiltinCommand(f"= {math_res}", "Copy to clipboard", "accessories-calculator-symbolic", f"wl-copy '{math_res}'")
            self._add_item(raw_cmd, is_cmd=True)
        
        all_searchable = self._all_apps + BUILTIN_COMMANDS + getattr(self, '_open_windows_cache', [])
        
        enhanced_results = []
        usage_data = load_usage()
        
        for item in all_searchable:
            name = getattr(item, 'display_name', None) or getattr(item, 'name', '')
            if not name:
                continue
                
            name_lower = name.lower()
            
            if query_lower in name_lower:
                base_score = 80
            else:
                base_score = fuzz.WRatio(query_lower, name_lower)
                if base_score < 40:
                    continue
                
            score = base_score
            
            if name_lower == query_lower:
                score += 1000
            elif name_lower.startswith(query_lower):
                score += 500
            elif any(word.startswith(query_lower) for word in re.split(r'[^a-zA-Z0-9]', name_lower)):
                score += 300
            elif query_lower in name_lower:
                score += 100
                
            if isinstance(item, BuiltinCommand) and item.description.startswith("Open Window"):
                score += 150
            elif not isinstance(item, BuiltinCommand):
                u_count = get_usage_count(item, usage_data)
                score += min(u_count * 5, 80)
                
            enhanced_results.append((item, score))
            
        enhanced_results.sort(key=lambda x: x[1], reverse=True)
        filtered = [item for item, score in enhanced_results][:12]
        self._populate(filtered)

    def _populate_default(self):
        bookmarks = load_bookmarks()
        all_items = self._all_apps + BUILTIN_COMMANDS
        
        favorite_apps = []
        for b_id in bookmarks:
            for item in all_items:
                if get_app_id(item) == b_id:
                    favorite_apps.append(item)
                    break
        
        usage = load_usage()
        sorted_apps = sorted(self._all_apps, key=lambda a: get_usage_count(a, usage), reverse=True)
        suggestions = [a for a in sorted_apps if a not in favorite_apps][:8]
        
        if favorite_apps:
            lbl = Label(label="Favorites", style_classes=["applauncher-header"], h_align="start")
            self.results_box.add(lbl)
            lbl.show()
            self._populate(favorite_apps, reset_selection=False)
            
        if suggestions:
            lbl = Label(label="Suggestions", style_classes=["applauncher-header"], h_align="start")
            self.results_box.add(lbl)
            lbl.show()
            self._populate(suggestions, reset_selection=False)
            
        self._selected_index = 0
        self._update_selection()

    def _populate(self, items, reset_selection=True):
        for item in items:
            is_cmd = isinstance(item, BuiltinCommand)
            self._add_item(item, is_cmd)
        if reset_selection:
            self._selected_index = 0
            self._update_selection()
            
    def _get_app_items(self):
        return [c for c in self.results_box.get_children() if isinstance(c, AppLauncherItem)]
        
    def _update_selection(self):
        items = self._get_app_items()
        if not items:
            return
            
        self._selected_index = max(0, min(self._selected_index, len(items) - 1))
        
        for i, item in enumerate(items):
            if i == self._selected_index:
                item.box.add_style_class("selected")
                adj = self.scrolled_window.get_vadjustment()
                allocation = item.get_allocation()

                def scroll_to_item(adj=adj, alloc=allocation):
                    if alloc.y < adj.get_value():
                        adj.set_value(alloc.y)
                    elif alloc.y + alloc.height > adj.get_value() + adj.get_page_size():
                        adj.set_value(alloc.y + alloc.height - adj.get_page_size())
                GLib.idle_add(scroll_to_item)
            else:
                item.box.remove_style_class("selected")
        
    def _activate_selected(self):
        items = self._get_app_items()
        if items and 0 <= self._selected_index < len(items):
            items[self._selected_index].launch()
            
    def _on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide_launcher()
            return True
        return False

    def _on_entry_key_press(self, widget, event):
        items = self._get_app_items()
        
        if event.state & Gdk.ModifierType.CONTROL_MASK and event.keyval in (Gdk.KEY_b, Gdk.KEY_B):
            if items and 0 <= self._selected_index < len(items):
                item = items[self._selected_index]._item
                app_id = get_app_id(item)
                toggle_bookmark(app_id)
                query = self.search_entry.get_text()
                self._search(query)
            return True
            
        if not items:
            return False
            
        if event.keyval in (Gdk.KEY_Down, Gdk.KEY_Tab):
            self._selected_index = min(len(items) - 1, self._selected_index + 1)
            self._update_selection()
            return True
        elif event.keyval in (Gdk.KEY_Up, Gdk.KEY_ISO_Left_Tab):
            self._selected_index = max(0, self._selected_index - 1)
            self._update_selection()
            return True
            
        return False
        
    def _fetch_open_windows(self):
        windows = []
        try:
            out = subprocess.check_output(["niri", "msg", "-j", "windows"], timeout=1).decode('utf-8')
            for w in json.loads(out):
                title = w.get("title", "")
                app_id = w.get("app_id", "")
                wid = w.get("id")
                
                name = f"{title}" if title else f"{app_id}"
                desc = f"Open Window ({app_id})"
                icon = app_id if app_id else "preferences-system-windows-symbolic"
                cmd = BuiltinCommand(name, desc, icon, f"niri msg action focus-window --id {wid}")
                windows.append(cmd)
        except Exception:
            pass
        return windows

    def show_launcher(self, page="launcher"):
        self._selected_index = 0
        self._just_opened = True
        
        if page == "launcher":
            self._stack.set_visible_child_name("launcher")
            self._emoji_toggle_btn.child = Image(
                icon_name="face-smile-symbolic", icon_size=16
            )
            self._emoji_toggle_btn.get_style_context().remove_class("active")
            self.search_entry.set_text("")
            self.show_all()
            self._search("")
            GLib.idle_add(self.search_entry.grab_focus)
        elif page == "emoji":
            self._stack.set_visible_child_name("emoji")
            self._emoji_page.reset()
            self._emoji_toggle_btn.child = Image(
                icon_name="view-grid-symbolic", icon_size=16
            )
            self._emoji_toggle_btn.get_style_context().add_class("active")
            self.show_all()
            GLib.idle_add(self._emoji_page._entry.grab_focus)
        GLib.timeout_add(300, self._clear_activation_lock)

        threading.Thread(target=self._async_fetch_windows, daemon=True).start()

    def _clear_activation_lock(self):
        self._just_opened = False
        return False  # don't repeat

    def _async_fetch_windows(self):
        windows = self._fetch_open_windows()
        def on_done():
            self._open_windows_cache = windows
            if self.get_visible() and not self.search_entry.get_text():
                self._search("")
        GLib.idle_add(on_done)
        
    def hide_launcher(self):
        self.hide()
