from fabric.widgets.box import Box
from fabric.utils.helpers import get_relative_path
from fabric import Fabricator

BAR_COUNT = 28

class CavaWidget(Box):
    def __init__(self, monitor_id, variant, **kwargs):
        self._bars = [Box(style_classes=["cava-bar"]) for _ in range(BAR_COUNT)]

        super().__init__(style_classes=["bar-button"], spacing=3, children=self._bars, **kwargs)
        
        self._fabricator = Fabricator(
            poll_from=f"cava -p {get_relative_path('./cava.ini')}",
            interval=0,
            stream=True,
            on_changed=self._on_update,
        )

    def _on_update(self, _, line: str) -> None:
        values = [
            int(v)
            for v in line.strip(";").split(";")
            if v.strip().isdigit()
        ]
        for value, bar in zip(values, self._bars):
            bar.set_style(
                f"* {{ margin-top: {17 - value}px;"
                f"border-radius: 10px; margin-bottom: {17 - value}px; }}",
                compile=False,
                add_brackets=False,
            )