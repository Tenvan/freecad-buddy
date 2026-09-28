"""Horizontal splitter between two stacked panes (Textual has no built-in one).

Drag it with the mouse; the pane below gets a fixed height, the pane above takes the rest.
"""

from __future__ import annotations

from textual import events
from textual.widget import Widget


class Splitter(Widget):
    DEFAULT_CSS = """
    Splitter {
        height: 1;
        width: 100%;
        background: $panel;
        color: $text-muted;
        content-align: center middle;
    }
    Splitter:hover, Splitter.-dragging { background: $accent; color: $text; }
    """

    def __init__(
        self, lower_id: str, *, min_lower: int = 3, min_upper: int = 5, id: str | None = None
    ) -> None:
        super().__init__(id=id)
        self.lower_id = lower_id
        self.min_lower = min_lower
        self.min_upper = min_upper
        self._dragging = False

    def render(self) -> str:
        return "━━━━━  ⇕ ziehen  ━━━━━"

    def on_mouse_down(self, event: events.MouseDown) -> None:
        self._dragging = True
        self.add_class("-dragging")
        self.capture_mouse()
        event.stop()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if self._dragging:
            self.resize_to(event.screen_y)
            event.stop()

    def on_mouse_up(self, event: events.MouseUp) -> None:
        if self._dragging:
            self._dragging = False
            self.remove_class("-dragging")
            self.release_mouse()
            event.stop()

    def lower_height(self) -> int:
        return self.screen.query_one(f"#{self.lower_id}").outer_size.height

    def resize_to(self, screen_y: int) -> int:
        """Place the splitter at ``screen_y``; returns the new height of the lower pane."""
        container = self.parent
        if not isinstance(container, Widget):
            return self.lower_height()
        region = container.region
        wanted = region.bottom - screen_y - self.outer_size.height
        return self.set_lower_height(wanted)

    def set_lower_height(self, rows: int) -> int:
        container = self.parent
        available = container.region.height if isinstance(container, Widget) else rows
        limit = max(self.min_lower, available - self.min_upper - self.outer_size.height)
        rows = max(self.min_lower, min(rows, limit))
        self.screen.query_one(f"#{self.lower_id}").styles.height = rows
        return rows
