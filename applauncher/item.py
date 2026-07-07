import subprocess
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.image import Image
from fabric.widgets.centerbox import CenterBox
from utils.dispatch import dispatch_app
from windows.launcher import increment_usage
from .commands import BuiltinCommand


class AppLauncherItem(Button):
    def __init__(self, launcher):
        self._item = None
        self._launcher = launcher
        self._is_custom_cmd = False

        self.icon_image = Image(icon_size=32)
        self.name_label = Label(style_classes=["app-name"], h_align="start")
        self.desc_label = Label(style_classes=["app-desc"], h_align="start")
        self.category_label = Label(style_classes=["app-category"])

        self.text_box = Box(
            orientation="v",
            spacing=0,
            v_align="center",
            children=[self.name_label, self.desc_label]
        )

        self.box = CenterBox(
            style_classes=["applauncher-item"],
            start_children=Box(
                spacing=16,
                children=[self.icon_image, self.text_box]
            ),
            end_children=self.category_label,
        )

        super().__init__(
            child=self.box,
            on_clicked=self.launch
        )
        self.connect("enter-notify-event", lambda *_: self.box.add_style_class("hover"))
        self.connect("leave-notify-event", lambda *_: self.box.remove_style_class("hover"))
        self.connect("focus-in-event", lambda *_: self.box.add_style_class("focus"))
        self.connect("focus-out-event", lambda *_: self.box.remove_style_class("focus"))

    def set_item(self, item, is_custom_cmd=False):
        self._item = item
        self._is_custom_cmd = is_custom_cmd
        self.icon_image.clear()

        icon = getattr(item, 'icon_name', None) or "application-x-executable"
        name = getattr(item, 'display_name', None) or getattr(item, 'name', '') or "Unknown"
        desc = getattr(item, 'description', '') or ''
        if not desc and hasattr(item, 'get_description'):
            try:
                desc = item.get_description() or ''
            except Exception:
                pass

        if not desc:
            desc = "Command" if is_custom_cmd else "Application"

        self.icon_image.set_from_icon_name(icon, 32)
        self.name_label.set_label(name)
        self.desc_label.set_label(desc)
        self.category_label.set_label("")

    def launch(self, *_):
        if self._item is None:
            return
        if getattr(self._launcher, '_just_opened', False):
            return

        if isinstance(self._item, BuiltinCommand) and self._item.name in ("Reboot", "Shutdown", "Sleep"):
            confirm_map = {
                "Reboot": "confirm reboot",
                "Shutdown": "confirm shutdown",
                "Sleep": "confirm sleep",
            }
            self._launcher.search_entry.set_text(confirm_map[self._item.name])
            return
        if self._is_custom_cmd and not getattr(self._item, 'command_line', '').strip():
            return

        if not self._is_custom_cmd:
            increment_usage(self._item)
            dispatch_app(self._item)
        else:
            subprocess.Popen(
                self._item.command_line,
                shell=True,
                start_new_session=True
            )

        self._launcher.hide_launcher()
