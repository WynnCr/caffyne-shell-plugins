"""Emoji Picker — searchable grid, click copies to clipboard via wl-copy."""
import json, os, subprocess
from gi.repository import Gtk, GLib

EMOJI_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "data", "emoji_history.json")

EMOJI_CATEGORIES = {
    "😀 Smileys": ["😀","😃","😄","😁","😆","😅","🤣","😂","🙂","🙃","😉","😊","😇","🥰","😍","🤩","😘","😗","😚","😙","🥲","😋","😛","😜","🤪","😝","🤑","🤗","🤭","🤫","🤔","🤐","🤨","😐","😑","😶","😏","😒","🙄","😬","🤥","😌","😔","😪","🤤","😴","😷","🤒","🤕","🤢","🤮","🤧","🥵","🥶","😵","🤯","🥳","😎","🤓","🧐","😕","😟","🙁","☹️","😮","😯","😲","😳","🥺","😦","😧","😨","😰","😥","😢","😭","😱","😖","😣","😞","😓","😩","😫","🥱","😤","😡","😠","🤬","😈","👿","💀","☠️","💩","🤡","👹","👺","👻","👽","👾","🤖"],
    "👋 People": ["👋","🤚","🖐️","✋","🖖","👌","🤌","🤏","✌️","🤞","🤟","🤘","🤙","👈","👉","👆","🖕","👇","☝️","👍","👎","✊","👊","🤛","🤜","👏","🙌","👐","🤲","🤝","🙏","✍️","💅","🤳","💪","🦾","👂","🦻","👃","👀","👅","👄","👶","🧒","👦","👧","🧑","👱","👨","🧔","👩","🧓","👴","👵","🙍","🙎","🙅","🙆","💁","🙋","🧏","🙇","🤦","🤷","👮","🕵️","💂","🥷","👷","🫅","🤴","👸","👳","👲","🧕","🤵","👰","🤰","🫃","🤱","👼","🎅","🤶","🦸","🦹","🧙","🧝","🧛","🧟","🧞","🧜","🧚","🧑‍🦯","🧑‍🦼","🧑‍🦽","🏃","🧎","🧍","🚶"],
    "🐶 Animals": ["🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷","🐸","🐵","🙈","🙉","🙊","🐔","🐧","🐦","🐤","🦆","🦅","🦉","🦇","🐺","🐗","🐴","🦄","🐝","🐛","🦋","🐌","🐞","🐜","🦟","🦗","🕷️","🦂","🐢","🐍","🦎","🐙","🦑","🦐","🦞","🦀","🐡","🐠","🐟","🐬","🐳","🐋","🦈","🐊","🐅","🐆","🦓","🐘","🦛","🦏","🐪","🦒","🦘","🐃","🐂","🐄","🐎","🐖","🐏","🐑","🦙","🐐","🦌","🐕","🐩","🐈","🐓","🦃","🦚","🦜","🦢","🦩","🕊️","🐇","🦝","🦦","🦥","🐁","🐀","🐿️","🦔","🌵","🌲","🌳","🌴","🌱","🌿","☘️","🍀","🍃","🍂","🍁","🍄","🌾","💐","🌷","🌹","🌺","🌸","🌼","🌻","🌞","🌝","🌙","⭐","🌈","⚡","🌊"],
    "🍔 Food": ["🍏","🍎","🍐","🍊","🍋","🍌","🍉","🍇","🍓","🫐","🍒","🍑","🥭","🍍","🥥","🥝","🍅","🍆","🥑","🥦","🥬","🥒","🌶️","🌽","🥕","🧄","🧅","🥔","🥐","🥯","🍞","🥖","🧀","🥚","🍳","🧈","🥞","🥓","🥩","🍗","🍖","🌭","🍔","🍟","🍕","🥪","🥙","🧆","🌮","🌯","🥗","🥘","🍝","🍜","🍲","🍛","🍣","🍱","🥟","🍤","🍙","🍚","🍘","🧁","🍰","🎂","🍮","🍭","🍬","🍫","🍿","🍩","🍪","🌰","🥜","🍯","🧃","🥤","🧋","☕","🍵","🍺","🍻","🥂","🍷","🥃","🍸","🍹","🧊"],
    "⚽ Activities": ["⚽","🏀","🏈","⚾","🥎","🎾","🏐","🏉","🎱","🏓","🏸","🏒","🏑","🥍","🏏","🥅","⛳","🎣","🤿","🥊","🥋","🎽","🛹","🛷","⛸️","🥌","🎿","⛷️","🏂","🏋️","🤸","⛹️","🏇","🧘","🏄","🏊","🤽","🚣","🧗","🚵","🚴","🏆","🥇","🥈","🥉","🏅","🎖️","🎫","🎟️","🎪","🤹","🎭","🩰","🎨","🎬","🎤","🎧","🎼","🎹","🥁","🎷","🎺","🎸","🎻","🎲","♟️","🎯","🎳","🎮","🎰","🧩"],
    "✈️ Travel": ["🚗","🚕","🚙","🚌","🏎️","🚓","🚑","🚒","🚜","🏍️","🛵","🚲","🛴","🛹","⛵","🚤","🛥️","🚢","✈️","🛩️","🪂","💺","🚁","🚀","🛸","🌍","🌎","🌏","🧭","🗺️","🏔️","⛰️","🌋","🏕️","🏖️","🏜️","🏝️","🏟️","🏛️","🏠","🏡","🏢","🏣","🏤","🏥","🏦","🏨","🏩","🏪","🏫","🏬","🏭","🏯","🏰","💒","🗼","🗽","⛪","🕌","⛩️","🕋","⛲","⛺","🌁","🌃","🏙️","🌄","🌅","🌆","🌇","🌉","🎠","🎡","🎢","🎪"],
    "💡 Objects": ["👓","🕶️","🌂","☂️","🧵","🪡","🧶","👔","👕","👖","🧣","🧤","🧥","🧦","👗","👘","👙","👛","👜","👝","🎒","🧳","👒","🎩","🧢","💄","💍","💎","📱","☎️","📞","💡","🔦","📺","📷","📸","📹","🔭","🔬","💊","💉","🩹","🪤","🧲","🪜","🛋️","🚪","🛏️","🛁","🚿","🧴","🧹","🧺","🧻","🧼","🧽","🧯","🛒","🎀","🎁","🎊","🎉","🎈","🎆","🎇","🧨","✨","🪄","🎋","🎍","🎎","🎐","🧧","🎑"],
    "❤️ Symbols": ["❤️","🧡","💛","💚","💙","💜","🖤","🤍","🤎","💔","❣️","💕","💞","💓","💗","💖","💘","💝","💟","☮️","✝️","☪️","🕉️","☸️","✡️","☯️","⛎","♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓","💯","💢","♨️","🚫","✅","☑️","✔️","❌","⭕","🔱","♻️","🔰","🆗","🆙","🆒","🆕","🆓","🔝","🔛","🔜","🔚","🔙","▶️","⏩","⏭️","⏯️","◀️","⏪","⏮️","🔼","⏫","🔽","⏬","⏸️","⏹️","⏺️","🎦","🔅","🔆","📶","🛜","🎵","🎶","💤","🔇","🔈","🔉","🔊","🔔","🔕"],
}

def _load_history():
    try:
        os.makedirs(os.path.dirname(EMOJI_HISTORY_FILE), exist_ok=True)
        if not os.path.exists(EMOJI_HISTORY_FILE):
            with open(EMOJI_HISTORY_FILE, "w") as f:
                json.dump([], f)
            return []
            
        with open(EMOJI_HISTORY_FILE) as f:
            return json.load(f)
    except Exception:
        pass
    return []

def _save_history(emoji):
    try:
        history = _load_history()
        if emoji in history:
            history.remove(emoji)
        history.insert(0, emoji)
        history = history[:32]
        os.makedirs(os.path.dirname(EMOJI_HISTORY_FILE), exist_ok=True)
        with open(EMOJI_HISTORY_FILE, "w") as f:
            json.dump(history, f)
    except Exception:
        pass


class EmojiPage(Gtk.Box):
    def __init__(self, hide_callback=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._active_category = None
        self._hide_callback = hide_callback  # called before typing emoji
        self._build_ui()
        self._show_all_or_recent()

    def _build_ui(self):
        self._entry = Gtk.Entry()
        self._entry.set_placeholder_text("Search emojis…")
        self._entry.get_style_context().add_class("emoji-search")
        self._entry.connect("changed", self._on_entry_changed)
        self._entry.connect("activate", self._on_entry_activated)
        self._entry.connect("key-press-event", self._on_entry_key_press)
        self.pack_start(self._entry, False, False, 0)
        self._pill_buttons = {}
        pill_scroll = Gtk.ScrolledWindow()
        pill_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        pill_scroll.set_size_request(-1, 44)
        pill_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        pill_box.get_style_context().add_class("emoji-pill-row")

        for cat in list(EMOJI_CATEGORIES.keys()):
            label = cat.split(" ")[0]  
            btn = Gtk.Button(label=label)
            btn.get_style_context().add_class("emoji-pill")
            btn.set_tooltip_text(cat.split(" ", 1)[-1])
            btn.connect("clicked", self._on_category_clicked, cat)
            self._pill_buttons[cat] = btn
            pill_box.pack_start(btn, False, False, 0)

        pill_scroll.add(pill_box)
        self.pack_start(pill_scroll, False, False, 8)

        self._scroll = Gtk.ScrolledWindow()
        self._scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._scroll.set_min_content_height(300)
        self._scroll.set_max_content_height(420)

        self._content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self._scroll.add(self._content_box)
        self.pack_start(self._scroll, True, True, 0)

        self.show_all()

    def _clear(self):
        for child in self._content_box.get_children():
            child.destroy()

    def _add_section(self, title, emojis):
        if not emojis:
            return

        lbl = Gtk.Label(label=title)
        lbl.set_halign(Gtk.Align.START)
        lbl.get_style_context().add_class("emoji-section-header")
        self._content_box.pack_start(lbl, False, False, 0)

        flow = Gtk.FlowBox()
        flow.set_max_children_per_line(10)
        flow.set_min_children_per_line(8)
        flow.set_selection_mode(Gtk.SelectionMode.SINGLE)
        flow.set_homogeneous(True)
        flow.get_style_context().add_class("emoji-flow")
        flow.connect("child-activated", self._on_flowbox_child_activated)
        flow.connect("selected-children-changed", self._on_flowbox_selection_changed)

        for emoji in emojis:
            btn = Gtk.Button(label=emoji)
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.get_style_context().add_class("emoji-btn")
            btn.connect("clicked", self._on_emoji_clicked, emoji)
            flow.add(btn)

        self._content_box.pack_start(flow, False, False, 0)
        self._content_box.show_all()

    def _show_all_or_recent(self):
        self._clear()
        recent = _load_history()
        if recent:
            self._add_section("Recently Used", recent[:16])
        for cat, emojis in EMOJI_CATEGORIES.items():
            self._add_section(cat.split(" ", 1)[-1], emojis)

    def _show_category(self, cat):
        self._clear()
        self._add_section(cat.split(" ", 1)[-1], EMOJI_CATEGORIES[cat])

    def _show_search(self, query):
        import unicodedata
        self._clear()
        q = query.lower()
        results = []
        for cat, emojis in EMOJI_CATEGORIES.items():
            for e in emojis:
                # Emojis can be multiple characters (ZWJ sequences). Combine their unicode names.
                name = ""
                for char in e:
                    try:
                        name += unicodedata.name(char).lower() + " "
                    except ValueError:
                        pass
                
                if q in name:
                    results.append(e)
        self._add_section(f"Results for \"{query}\"", results[:80])
    def _on_flowbox_selection_changed(self, active_flowbox):
        # If this flowbox got selected, clear the selection in all other flowboxes
        if not active_flowbox.get_selected_children():
            return
            
        for child in self._content_box.get_children():
            if isinstance(child, Gtk.FlowBox) and child != active_flowbox:
                child.unselect_all()

    def _on_flowbox_child_activated(self, flowbox, child):
        # Triggered when pressing Enter on a keyboard-focused emoji
        btn = child.get_child()
        if btn:
            btn.emit("clicked")

    def _on_entry_activated(self, entry):
        # Auto-select the very first emoji when pressing Enter in search
        for child in self._content_box.get_children():
            if isinstance(child, Gtk.FlowBox):
                flow_children = child.get_children()
                if flow_children:
                    btn = flow_children[0].get_child()
                    if btn:
                        btn.emit("clicked")
                        return

    def _on_entry_key_press(self, entry, event):
        from gi.repository import Gdk
        if event.keyval == Gdk.KEY_Down:
            # Jump focus from search bar to the first emoji in the grid
            for child in self._content_box.get_children():
                if isinstance(child, Gtk.FlowBox):
                    flow_children = child.get_children()
                    if flow_children:
                        flow_children[0].grab_focus()
                        return True
        return False

    def _on_entry_changed(self, entry):
        self._on_search(entry.get_text())

    def _on_search(self, text):
        if not text:
            if self._active_category:
                self._show_category(self._active_category)
            else:
                self._show_all_or_recent()
        else:
            self._show_search(text)

    def _on_category_clicked(self, btn, cat):
        for b in self._pill_buttons.values():
            b.get_style_context().remove_class("active")
            
        is_clearing_text = bool(self._entry.get_text())
            
        if self._active_category == cat:
            self._active_category = None
            if not is_clearing_text:
                self._show_all_or_recent()
        else:
            self._active_category = cat
            btn.get_style_context().add_class("active")
            if not is_clearing_text:
                self._show_category(cat)
                
        if is_clearing_text:
            self._entry.set_text("")
            
        self._entry.grab_focus()

    def _on_emoji_clicked(self, btn, emoji):
        subprocess.Popen(["wl-copy", emoji], start_new_session=True)
        _save_history(emoji)
        
        if self._hide_callback:
            self._hide_callback()
        GLib.timeout_add(350, lambda: self._type_emoji(emoji))

    @staticmethod
    def _type_emoji(emoji):
        """Use Primary Selection + Shift+Insert to paste.
        - Terminals ignore Ctrl+V (requires Ctrl+Shift+V)
        - Browsers support Ctrl+V
        - ALL Linux apps (terminals, browsers, GTK/Qt) support Shift+Insert pasting from the primary selection.
        """
        try:
            subprocess.Popen(["wl-copy", "-p", emoji], start_new_session=True).wait()
            subprocess.Popen(["wtype", "-M", "shift", "-k", "Insert", "-m", "shift"], start_new_session=True)
        except FileNotFoundError:
            pass
        return False

    def _refresh_if_default(self):
        if not self._entry.get_text() and not self._active_category:
            self._show_all_or_recent()
        return False

    def reset(self):
        """Called when the emoji page is shown/hidden."""
        self._entry.set_text("")
        self._active_category = None
        for b in self._pill_buttons.values():
            b.get_style_context().remove_class("active")
        self._show_all_or_recent()
