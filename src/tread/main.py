"""Main entry point for tRead - Terminal EPUB Reader."""

import os
from typing import List, Dict, Optional

from .core.reader import load_book
from .core.bookmarks import BookmarkManager
from .utils.terminal import get_key, CursorManager
from .ui.controller import display_book
from rich.console import Console
from rich.table import Table

BOOKS_DIR = "books"
console = Console()


def list_epub_files() -> List[str]:
    """Get list of EPUB files in the books directory.

    Returns:
        List of EPUB filenames.
    """
    try:
        return [f for f in os.listdir(BOOKS_DIR) if f.lower().endswith(".epub")]
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

    for fname in epub_files:
        try:
            book = load_book(os.path.join(BOOKS_DIR, fname))
            has_cover = get_cover_info(book)
            has_bookmark = bookmark_manager.has_bookmark(book.metadata["title"])
            books.append(
                {
                    "filename": fname,
                    "title": book.metadata["title"],
                    "author": book.metadata["author"],
                    "has_cover": has_cover,
                    "has_bookmark": has_bookmark,
                }
            )
        except Exception as e:
            books.append(
                {
                    "filename": fname,
                    "title": "[Error reading]",
                    "author": str(e),
                    "has_cover": False,
                    "has_bookmark": False,
                }
            )
    return books


def display_book_selection_table(books: List[Dict[str, any]], selected: int) -> None:
    """Display the book selection table.

    Args:
        books: List of book information dictionaries.
        selected: Index of currently selected book.
    """
    table = Table(title="Select a Book", show_lines=True)
    table.add_column("#", justify="right")
    table.add_column("Title")
    table.add_column("Author")
    table.add_column("Cover")
    table.add_column("Bookmark")

    for i, book in enumerate(books):
        marker = ">" if i == selected else " "
        cover = "Yes" if book["has_cover"] else "No"
        bookmark = "[green]Yes[/green]" if book["has_bookmark"] else "No"
        table.add_row(f"{marker} {i+1}", book["title"], book["author"], cover, bookmark)

    console.clear()
    console.print(table)
    console.print("Use ↑/↓ to select, Enter to open, q to quit.")
    console.print(
        "[dim]Books with bookmarks will automatically load to saved position.[/dim]"
    )


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


def pick_book() -> Optional[str]:
    """Interactive book selection interface.

    Returns:
        Path to selected book file, or None if cancelled.
    """
    epub_files = list_epub_files()
    if not epub_files:
        console.print("[red]No EPUB files found in the books folder![/red]")
        return None

    books = build_book_info_list(epub_files)
    selected = 0

    while True:
        display_book_selection_table(books, selected)
        key = get_key().lower()
        action, selected = handle_book_selection_input(key, selected, len(books))

        if action == "quit":
            return None
        elif action == "select":
            return os.path.join(BOOKS_DIR, books[selected]["filename"])


def main() -> None:
    """Main entry point for the application."""
    try:
        with CursorManager():
            book_path = pick_book()
            if book_path:
                epub_book = load_book(book_path)
                display_book(epub_book)
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    main()
