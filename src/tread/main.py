"""Main entry point for tRead - Terminal EPUB Reader."""

import os
from typing import List, Dict, Optional

from .core.reader import load_book
from .core.bookmarks import BookmarkManager
from .core.config import get_config
from .utils.terminal import get_key, CursorManager
from .utils.colors import StyledConsole
from .ui.state import DisplayCalculator
from rich.console import Console
from rich.panel import Panel


def get_books_dir() -> str:
    config = get_config()
    books_dir = config._config_data.get("books_dir", "books")
    if not books_dir:
        books_dir = "books"
    # Use the directory containing config.json as project root
    config_path = config.config_path if hasattr(config, 'config_path') else None
    if config_path:
        project_root = os.path.dirname(os.path.abspath(config_path))
    else:
        project_root = os.getcwd()
    abs_books_dir = os.path.join(project_root, books_dir) if not os.path.isabs(books_dir) else books_dir
    return abs_books_dir


def get_console() -> StyledConsole:
    """Get a styled console instance with color configuration applied."""
    console = Console(highlight=False, color_system="truecolor")
    return StyledConsole(console)


def list_epub_files() -> List[str]:
    """Get list of EPUB files in the books directory.

    Returns:
        List of EPUB filenames.
    """
    books_dir = get_books_dir()
    try:
        return [f for f in os.listdir(books_dir) if f.lower().endswith(".epub")]
    except FileNotFoundError:
        return []


def get_cover_info(epub_book) -> bool:
    """Check if the EPUB book has a cover image.

    Args:
        epub_book: EpubBook instance to check.

    Returns:
        True if cover exists, False otherwise.
    """
    try:
        for item in epub_book.book.get_items():
            if item.get_type() == 9 and "cover" in item.get_name().lower():
                return True
    except AttributeError:
        pass
    return False


def build_book_info_list(epub_files: List[str]) -> List[Dict[str, any]]:
    """Build a list of book information dictionaries.

    Args:
        epub_files: List of EPUB filenames.

    Returns:
        List of dictionaries containing book metadata.
    """
    books = []
    bookmark_manager = BookmarkManager()

    books_dir = get_books_dir()
    for fname in epub_files:
        try:
            book = load_book(os.path.join(books_dir, fname))
            has_cover = get_cover_info(book)

            # Calculate reading progress
            progress = 0
            if bookmark_manager.has_bookmark(book.metadata["title"]):
                bookmark = bookmark_manager.load_bookmark(book.metadata["title"])
                if bookmark and len(book.chapters) > 0:
                    # Rough progress calculation based on chapter completion
                    progress = int((bookmark.chapter / len(book.chapters)) * 100)

            books.append(
                {
                    "filename": fname,
                    "title": book.metadata["title"],
                    "author": book.metadata["author"],
                    "has_cover": has_cover,
                    "progress": progress,
                }
            )
        except Exception as e:
            books.append(
                {
                    "filename": fname,
                    "title": "[Error reading]",
                    "author": str(e),
                    "has_cover": False,
                    "progress": 0,
                }
            )
    return books


def display_book_selection_table(
    books: List[Dict[str, any]], selected: int, console: StyledConsole
) -> None:
    """Display the book selection menu.

    Args:
        books: List of book information dictionaries.
        selected: Index of currently selected book.
        console: Rich Console instance.
    """
    panel_width, _, visible_height, _ = DisplayCalculator.get_display_dimensions()

    # Calculate display window
    # Each book takes 3 lines (title, author, empty line)
    # Reserve space for ASCII art (6 lines), "Your Library" (2 lines), instructions (2 lines), scroll indicators (2 lines)
    header_lines = 12
    available_lines = visible_height - header_lines
    books_per_screen = available_lines // 3  # Each book takes 3 lines

    half_screen = books_per_screen // 2
    scroll_offset = max(0, selected - half_screen)
    scroll_offset = min(scroll_offset, max(0, len(books) - books_per_screen))

    # ASCII art header
    ascii_art = [
        "╔╦╗╦═╗╔═╗╔═╗╔╦╗",
        " ║ ╠╦╝║╣ ╠═╣ ║║",
        " ╩ ╩╚═╚═╝╩ ╩═╩╝",
        "",
        "[dim]Terminal EPUB Reader[/dim]",
        "",
    ]

    # Build book list
    book_lines = []
    book_lines.extend(ascii_art)
    book_lines.extend(["Your Library", ""])

    start_idx = scroll_offset
    end_idx = min(start_idx + books_per_screen, len(books))

    for i in range(start_idx, end_idx):
        book = books[i]
        marker = "►" if i == selected else " "

        # Progress indicator
        progress = book.get("progress", 0)
        if progress > 0:
            progress_bar = f"{progress:3d}%"
        else:
            progress_bar = ""

        # Format book entry
        title = book["title"][:40] + "..." if len(book["title"]) > 40 else book["title"]
        author = (
            book["author"][:25] + "..." if len(book["author"]) > 25 else book["author"]
        )

        book_lines.append(f"{marker} [bold]{title}[/bold]")
        book_lines.append(f"    [dim]by {author}[/dim] {progress_bar}")
        book_lines.append("")

    # Add scroll indicators
    if start_idx > 0:
        # Find the first book line after ascii art
        first_book_line = len(ascii_art) + 2
        book_lines[first_book_line] = "    [dim]... (more books above)[/dim]"
    if end_idx < len(books):
        book_lines.append("    [dim]... (more books below)[/dim]")

    book_lines.append("")

    # Pad to fill screen
    while len(book_lines) < visible_height:
        book_lines.append("")

    console.clear()

    # Check if borders should be shown
    config = get_config()
    show_border = config.display.get("show_border", True)

    if show_border:
        console.print(
            Panel(
                "\n".join(book_lines),
                title="",
                padding=(
                    DisplayCalculator.PANEL_PADDING_Y,
                    DisplayCalculator.get_panel_padding_x(),
                ),
                width=panel_width + 2 if panel_width > 0 else None,
            )
        )
    else:
        # Display without border
        padding_x = DisplayCalculator.get_panel_padding_x()
        padding_spaces = " " * padding_x

        # Display content with padding
        for line in book_lines:
            if line.strip():  # Don't pad empty lines
                console.print(f"{padding_spaces}{line}")
            else:
                console.print()


def handle_book_selection_input(
    key: str, selected: int, max_books: int
) -> tuple[Optional[str], int]:
    """Handle input for book selection.

    Args:
        key: The pressed key.
        selected: Currently selected book index.
        max_books: Total number of books.

    Returns:
        Tuple of (action, new_selected_index). Action can be 'quit', 'select', or None.
    """
    if key == "q":
        return "quit", selected
    elif key == "\r":  # Enter
        return "select", selected
    elif key in ["j", "\x1b[B"]:  # Down
        return None, min(selected + 1, max_books - 1)
    elif key in ["k", "\x1b[A"]:  # Up
        return None, max(selected - 1, 0)

    return None, selected


def pick_book(console: StyledConsole) -> Optional[str]:
    """Interactive book selection interface.

    Args:
        console: Rich Console instance.

    Returns:
        Path to selected book file, or None if cancelled.
    """
    books_dir = get_books_dir()
    epub_files = list_epub_files()
    if not epub_files:
        console.print(f"[red]No EPUB files found in the books folder: {books_dir}![/red]")
        return None

    books = build_book_info_list(epub_files)
    selected = 0

    while True:
        display_book_selection_table(books, selected, console)
        key = get_key().lower()
        action, selected = handle_book_selection_input(key, selected, len(books))

        if action == "quit":
            # Show quit confirmation in the panel
            panel_width, _, visible_height, _ = (
                DisplayCalculator.get_display_dimensions()
            )

            # Build quit confirmation display
            ascii_art = [
                "╔╦╗╦═╗╔═╗╔═╗╔╦╗",
                " ║ ╠╦╝║╣ ╠═╣ ║║",
                " ╩ ╩╚═╚═╝╩ ╩═╩╝",
                "",
                "[dim]Terminal EPUB Reader - press h to see available commands[/dim]",
                "",
            ]

            quit_lines = []
            quit_lines.extend(ascii_art)
            quit_lines.extend(["", "[bold]Really quit tRead? (Y/n)[/bold]", ""])

            # Pad to fill screen
            while len(quit_lines) < visible_height:
                quit_lines.append("")

            console.clear()

            # Check if borders should be shown
            config = get_config()
            show_border = config.display.get("show_border", True)

            if show_border:
                console.print(
                    Panel(
                        "\n".join(quit_lines),
                        title="",
                        subtitle="[bold]Really quit tRead? (Y/n)[/bold]",
                        subtitle_align="center",
                        padding=(
                            DisplayCalculator.PANEL_PADDING_Y,
                            DisplayCalculator.get_panel_padding_x(),
                        ),
                        width=panel_width + 2 if panel_width > 0 else None,
                    )
                )
            else:
                # Display without border - center content manually
                padding_x = DisplayCalculator.get_panel_padding_x()
                padding_spaces = " " * padding_x

                # Display content with padding
                for line in quit_lines:
                    if line.strip():  # Don't pad empty lines
                        console.print(f"{padding_spaces}{line}")
                    else:
                        console.print()

                # Display subtitle/notification - center it manually
                console.print()
                subtitle_text = "[bold]Really quit tRead? (Y/n)[/bold]"
                subtitle_plain = "Really quit tRead? (Y/n)"
                subtitle_width = len(subtitle_plain)
                available_width = panel_width - (2 * padding_x)
                subtitle_padding = max(0, (available_width - subtitle_width) // 2)
                subtitle_spaces = " " * (padding_x + subtitle_padding)
                console.print(f"{subtitle_spaces}{subtitle_text}")

            confirm = get_key().lower()
            if confirm in ["n", "no"]:
                continue
            else:
                return None
        elif action == "select":
            return os.path.join(get_books_dir(), books[selected]["filename"])


def main() -> None:
    """Main entry point for the application."""
    console = get_console()

    try:
        with CursorManager():
            while True:
                book_path = pick_book(console)
                if not book_path:
                    break
                epub_book = load_book(book_path)
                from .ui.controller import UIController

                controller = UIController(epub_book)
                return_to_menu = controller.run()
                controller.save_auto_bookmark()
                if not return_to_menu:
                    break
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
    except Exception as e:
        # Escape any Rich markup in the error message to prevent markup errors
        error_msg = str(e).replace("[", "\\[").replace("]", "\\]")
        console.print(f"[red]Error: {error_msg}[/red]")


if __name__ == "__main__":
    main()
