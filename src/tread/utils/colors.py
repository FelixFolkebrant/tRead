"""Color and styling utilities for tRead."""

from rich.style import Style
from rich.console import Console

from ..core.config import get_config


class StyledConsole:
    """Wrapper around Rich Console that applies color configuration automatically."""

    def __init__(self, console: Console):
        self.console = console
        self.base_style = self._get_base_style()

    def _get_base_style(self) -> Style:
        """Get the base style with configured colors."""
        config = get_config()
        colors = config.display.get("colors", {})

        text_color = colors.get("text", "")
        background_color = colors.get("background", "")

        return Style(
            color=text_color if text_color else None,
            bgcolor=background_color if background_color else None,
        )

    def print(self, *args, style=None, **kwargs):
        """Print with base styling applied."""
        if style is None:
            style = self.base_style
        elif self.base_style and style:
            # Combine base style with custom style
            style = self.base_style + style
        elif self.base_style:
            style = self.base_style

        self.console.print(*args, style=style, **kwargs)

    def clear(self):
        """Clear console and apply background if configured."""
        config = get_config()
        colors = config.display.get("colors", {})
        background_color = colors.get("background", "")

        if background_color:
            # Clear with background color
            from ..utils.terminal import get_terminal_size

            width, height = get_terminal_size()

            # Clear screen
            import sys

            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()

            # Fill with background color
            bg_style = Style(bgcolor=background_color)
            for _ in range(height):
                self.console.print(" " * width, style=bg_style, end="")

            # Reset cursor to top
            sys.stdout.write("\033[H")
            sys.stdout.flush()
        else:
            # Regular clear
            self.console.clear()

    def __getattr__(self, name):
        """Delegate other methods to the underlying console."""
        return getattr(self.console, name)


def get_style(element: str = "text") -> Style:
    """Get Rich Style object for a specific UI element.

    Args:
        element: The UI element to style ('text', 'background', 'border', 'title')

    Returns:
        Rich Style object with the configured colors, or default if not specified.
    """
    config = get_config()
    colors = config.display.get("colors", {})

    background_color = colors.get("background", "")
    text_color = colors.get("text", "")
    border_color = colors.get("border", "")
    if element == "text":
        return Style(
            color=text_color if text_color else None,
            bgcolor=background_color if background_color else None,
        )
    elif element == "border":
        return Style(
            color=border_color if border_color else text_color if text_color else None,
            bgcolor=background_color if background_color else None,
        )
    elif element == "background":
        return Style(bgcolor=background_color if background_color else None)
    else:
        return Style(
            color=text_color if text_color else None,
            bgcolor=background_color if background_color else None,
        )


def apply_background_to_console(console: Console) -> None:
    """Apply background color to the console if configured.

    Args:
        console: Rich Console instance to apply background to.
    """
    config = get_config()
    colors = config.display.get("colors", {})
    background_color = colors.get("background", "")

    if background_color:
        # Set console background using Rich style
        # Clear screen first
        import sys

        sys.stdout.write("\033[2J\033[H")  # Clear screen and move cursor to top
        sys.stdout.flush()

        # Print background colored space to fill screen
        from ..utils.terminal import get_terminal_size

        width, height = get_terminal_size()

        # Create a style with background color
        bg_style = Style(bgcolor=background_color)

        # Fill the screen with background colored spaces
        for _ in range(height):
            console.print(" " * width, style=bg_style, end="")

        # Reset cursor to top
        sys.stdout.write("\033[H")
        sys.stdout.flush()


def get_console_style() -> Style:
    """Get the base console style with configured colors.

    Returns:
        Rich Style object with configured text and background colors.
    """
    config = get_config()
    colors = config.display.get("colors", {})

    text_color = colors.get("text", "")
    background_color = colors.get("background", "")

    return Style(
        color=text_color if text_color else None,
        bgcolor=background_color if background_color else None,
    )


def get_styled_text(text: str, element: str = "text") -> str:
    """Get text with Rich markup for styling.

    Args:
        text: The text to style
        element: The UI element type ('text', 'border', 'title')

    Returns:
        Text with Rich markup applied, or original text if no styling.
    """
    config = get_config()
    colors = config.display.get("colors", {})

    if element == "border":
        color = colors.get("border", "") or colors.get("text", "")
        if color:
            return f"[{color}]{text}[/{color}]"
    elif element == "text":
        color = colors.get("text", "")
        if color:
            return f"[{color}]{text}[/{color}]"
    return text
