"""UI view components for tRead."""

from typing import List, Dict
from rich.console import Console
from rich.panel import Panel

from ..core.config import get_config
from ..utils.terminal import get_key
from .state import DisplayCalculator


def display_help_screen(console: Console) -> None:
    """Display the help screen with keybindings.

    Args:
        console: Rich Console instance.
    """
    keybinds = get_config().keybinds
    panel_width, _, visible_height, _ = DisplayCalculator.get_display_dimensions()

    help_lines = ["[bold]Keybinds[/bold]", ""]

    # Group keybinds by category for better organization
    navigation_keys = {
        "next_page": "Next page",
        "prev_page": "Previous page",
        "next_chapter": "Next chapter",
        "prev_chapter": "Previous chapter",
        "start": "Go to start",
        "end": "Go to end",
    }

    bookmark_keys = {
        "bookmark_save": "Save bookmark",
        "bookmark_goto": "Go to bookmark",
    }

    menu_keys = {
        "chapter_menu": "Chapter menu",
        "help": "Help",
        "quit": "Quit",
    }

    help_lines.extend(["[bold yellow]Navigation[/bold yellow]"])
    for action, description in navigation_keys.items():
        if action in keybinds:
            key_list = ", ".join(repr(k).replace("'", "") for k in keybinds[action])
            help_lines.append(f"  [bold]{description}[/bold]: {key_list}")

    help_lines.extend(["", "[bold green]Bookmarks[/bold green]"])
    for action, description in bookmark_keys.items():
        if action in keybinds:
            key_list = ", ".join(repr(k).replace("'", "") for k in keybinds[action])
            help_lines.append(f"  [bold]{description}[/bold]: {key_list}")

    help_lines.extend(["", "[bold blue]Menu/System[/bold blue]"])
    for action, description in menu_keys.items():
        if action in keybinds:
            key_list = ", ".join(repr(k).replace("'", "") for k in keybinds[action])
            help_lines.append(f"  [bold]{description}[/bold]: {key_list}")

    help_lines.extend(["", "Press any key to return."])

    # Pad to fill screen
    while len(help_lines) < visible_height:
        help_lines.append("")

    console.clear()
    console.print(
        Panel(
            "\n".join(help_lines),
            title="Help",
            padding=(
                DisplayCalculator.PANEL_PADDING_Y,
                DisplayCalculator.PANEL_PADDING_X,
            ),
            width=panel_width + 2 if panel_width > 0 else None,
        )
    )
    get_key()  # Wait for any key


def display_chapter_menu(
    console: Console, epub_book, current_chapter: int
) -> tuple[bool, int]:
    keybinds = get_config().keybinds
    panel_width, _, visible_height, _ = DisplayCalculator.get_display_dimensions()

    # Calculate chapter display window
    available_lines = visible_height - 4  # Reserve space for title, instructions
    half_screen = available_lines // 2
    scroll_offset = max(0, current_chapter - half_screen)
    scroll_offset = min(
        scroll_offset, max(0, len(epub_book.chapters) - available_lines)
    )

    # Build chapter list
    chapter_lines = ["[bold]Table of Contents[/bold]", ""]

    start_idx = scroll_offset
    end_idx = min(start_idx + available_lines, len(epub_book.chapters))

    for i in range(start_idx, end_idx):
        chapter = epub_book.chapters[i]
        marker = ">" if i == current_chapter else " "
        chapter_lines.append(f"{marker} {i+1:2d}. {chapter['title']}")

    # Add scroll indicators
    if start_idx > 0:
        chapter_lines[2] = "... (more chapters above)"
    if end_idx < len(epub_book.chapters):
        chapter_lines.append("... (more chapters below)")

    chapter_lines.append("")
    chapter_lines.append("Press Enter to select, 'c' to close, ↑↓ to navigate")

    # Pad to fill screen
    while len(chapter_lines) < visible_height:
        chapter_lines.append("")

    console.clear()
    console.print(
        Panel(
            "\n".join(chapter_lines),
            title=f"{epub_book.metadata['title']} - by {epub_book.metadata['author']} | Chapter {current_chapter + 1}/{len(epub_book.chapters)}",
            padding=(
                DisplayCalculator.PANEL_PADDING_Y,
                DisplayCalculator.PANEL_PADDING_X,
            ),
            width=panel_width + 2 if panel_width > 0 else None,
        )
    )

    key = get_key().lower()

    if key in keybinds["chapter_menu_close"]:
        return True, current_chapter
    elif key in keybinds["chapter_menu_select"]:  # Enter key
        return True, current_chapter  # Selection confirmed
    elif key in keybinds["chapter_menu_down"]:
        new_chapter = min(current_chapter + 1, len(epub_book.chapters) - 1)
        return False, new_chapter
    elif key in keybinds["chapter_menu_up"]:
        new_chapter = max(current_chapter - 1, 0)
        return False, new_chapter
    elif key in keybinds.get("help", []):
        display_help_screen(console)
        return False, current_chapter

    return False, current_chapter


def display_reading_page(
    console: Console,
    epub_book,
    state,
    page_content: List[str],
    progress_info: Dict[str, int],
    current_page: int,
    total_pages: int,
) -> None:
    panel_width, _, _, _ = DisplayCalculator.get_display_dimensions()

    chapter = state.get_current_chapter()
    overall_progress = progress_info["overall_progress"]

    # Book name and progress (upper left)
    book_name = (
        epub_book.metadata["title"]
        if hasattr(epub_book, "metadata") and "title" in epub_book.metadata
        else "Book"
    )
    book_info = f"{book_name} [{overall_progress}%]"

    chapter_name = chapter["title"] if chapter and "title" in chapter else "Chapter"
    chapter_info = f"{chapter_name} ({current_page + 1}/{total_pages})"

    upper_bar = f"{book_info} | {chapter_info}"

    # Display notification if present in state
    notification = getattr(state, "notification", None)
    if notification:
        subtitle = notification
        subtitle_align = "center"
    else:
        subtitle = ""
        subtitle_align = "center"

    console.clear()
    console.print(
        Panel(
            "\n".join(page_content),
            title=upper_bar,
            title_align="center",
            subtitle=subtitle,
            subtitle_align=subtitle_align,
            padding=(
                DisplayCalculator.PANEL_PADDING_Y,
                DisplayCalculator.PANEL_PADDING_X,
            ),
            width=panel_width + 2 if panel_width > 0 else None,
        )
    )

    # Clear notification after displaying it once
    if notification:
        state.notification = None
