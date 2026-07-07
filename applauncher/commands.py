class BuiltinCommand:
    def __init__(self, name, description, icon_name, command_str):
        self.name = name
        self.display_name = name
        self.description = description
        self.icon_name = icon_name
        self.command_line = command_str

BUILTIN_COMMANDS = [
    BuiltinCommand("Clipboard History", "View clipboard history", "edit-paste-symbolic", "cliphist list | wofi -d | cliphist decode | wl-copy"),
    BuiltinCommand("Refresh Apps", "Reload the shell", "view-refresh-symbolic", "pkill -f caffyne-shell && nix run"),
    BuiltinCommand("Lock Screen", "Lock the current session", "system-lock-screen-symbolic", "loginctl lock-session"),
    BuiltinCommand("Settings", "Open System Settings", "preferences-system-symbolic", "gnome-control-center"),
    BuiltinCommand("Read Manual", "View Caffyne Shell User Guide", "help-browser-symbolic", "xdg-open 'https://wynncr.notion.site/caffyne-spotlight'"),
    BuiltinCommand("Reboot", "Restart the computer", "system-reboot-symbolic", "systemctl reboot"),
    BuiltinCommand("Shutdown", "Power off the computer", "system-shutdown-symbolic", "systemctl poweroff"),
    BuiltinCommand("Sleep", "Suspend the computer", "system-suspend-symbolic", "systemctl suspend"),
]
