import time
from fabric.widgets.eventbox import EventBox
from fabric.widgets.box import Box
from snippets import Icon
from .window import get_launcher_window

class LauncherButton(EventBox):
    def __init__(self, monitor_id, variant, **kwargs):
        self.launcher_win = get_launcher_window()
        
        inner_box = Box(
            children=[Icon(icon_name="magnifying-glass-duotone", icon_size=18)],
            style_classes=["bar-button", "variant-icon"],
            h_align="center",
            v_align="center"
        )
        
        super().__init__(
            child=inner_box,
            **kwargs
        )
        self.connect("button-release-event", self._on_release)

    def _on_release(self, widget, event):
        # Allow parent to handle right clicks or edit mode drags
        if event.button != 1:
            return False
        
        # Check if in edit mode (don't activate if we are moving it)
        try:
            from bar_widgets.edit_mode import edit_mode
            if edit_mode.edit_mode:
                return False
        except ImportError:
            pass

        self._toggle()
        return True
        
    def _toggle(self, *_):
        now = time.time()

        if self.launcher_win.get_visible():
            # Debounce: ignore rapid hide requests within 800ms of opening
            # to prevent accidental close when double-clicking the bar button
            last = getattr(self, '_last_show_time', 0)
            if last and (now - last) < 0.8:
                return
            self.launcher_win.hide_launcher()
        else:
            self._last_show_time = now
            self.launcher_win.show_launcher()
