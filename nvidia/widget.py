from fabric.core.fabricator import Fabricator
from bar_widgets import ProgressButton # Base class
from snippets import Icon

class NvidiaWidget(ProgressButton):
    def __init__(self, monitor_id, vertical, variant=None, **kwargs):
        super().__init__(
            icon=lambda size: Icon(icon_name="graphics-card-duotone", icon_size=size),
            label="0%",
            variant=variant or "icon+label", # default variant
            **kwargs,
        )
        self.fabricator = Fabricator(
            poll_from="nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits",
            interval=2000,
        )
        self.fabricator.connect("changed", self._update)

    def _update(self, _, value):
        v = float(value.strip())
        self._update_label(f"{round(v)}%")
        self._update_value(v)