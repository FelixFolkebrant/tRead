"""Main UI controller for tRead."""

from rich.console import Console

from ..core.config import get_config
from ..utils.terminal import get_key
from .state import ReadingState, DisplayCalculator, PageManager
from .views import display_help_screen, display_chapter_menu, display_reading_page


class UIController:
    """Main UI controller that handles user input and coordinates displays."""

    def __init__(self, epub_book):
        """Initialize UI controller.

        Args:
            epub_book: EpubBook instance to display.
        """
        self.console = Console()
        self.state = ReadingState(epub_book)
        self.page_manager = PageManager(self.state)
        self.keybinds = get_config().keybinds
        self.config = get_config()

    def run(self) -> bool:
        """Main UI loop. Returns True if user wants to return to book select, False to exit."""
        # Auto-load bookmark if enabled
        if self.config.bookmarks.get("auto_load_bookmark_on_open", True):
            self.state.load_bookmark()

        while True:
            if self.state.show_help:
                display_help_screen(self.console)
                self.state.show_help = False
                continue

            if self.state.show_chapter_list:
                should_close, new_chapter = display_chapter_menu(
                    self.console, self.state.epub_book, self.state.current_chapter
                )
                if should_close:
                    self.state.show_chapter_list = False
                    self.state.current_page = (
                        0  # Reset to first page when selecting chapter
                    )
                else:
                    self.state.current_chapter = new_chapter
                continue

            # Regular reading mode
            if not self.state.epub_book.chapters:
                self.console.clear()
                self.console.print("No chapters found in this book.")
                break

            if not self._display_current_page():
                # User pressed quit
                return True
        return False

    def save_auto_bookmark(self) -> None:
        """Save current position as auto-bookmark on exit."""
        if self.config.bookmarks.get("auto_bookmark_on_exit", True):
            if self.state.save_bookmark():
                self.state.notification = "[green]Auto-saved bookmark[/green]"

    def _display_current_page(self) -> bool:
        """Display current page and handle input.

        Returns:
            False if user wants to quit, True to continue.
        """
        # Get display dimensions
        panel_width, text_width, visible_height, _ = (
            DisplayCalculator.get_display_dimensions()
        )

        # Get current pages and progress
        pages, progress_info = self.page_manager.get_current_pages(
            text_width, visible_height
        )

        # Handle empty pages
        if not pages:
            page_content = [""]
            current_page = 0
            total_pages = 1
        else:
            page_content = pages[self.state.current_page]
            current_page = self.state.current_page
            total_pages = len(pages)

        # Display the page
        display_reading_page(
            self.console,
            self.state.epub_book,
            self.state,
            page_content,
            progress_info,
            current_page,
            total_pages,
        )

        # Handle user input
        return self._handle_reading_input(pages, text_width, visible_height)

    def _handle_reading_input(
        self, pages, text_width: int, visible_height: int
    ) -> bool:
        """Handle user input during reading.

        Args:
            pages: Current chapter pages.
            text_width: Width for text wrapping.
            visible_height: Height for pagination.

        Returns:
            False if user wants to quit, True to continue.
        """
        key = get_key().lower()

        if key in self.keybinds["quit"]:
            return False
        elif key in self.keybinds["chapter_menu"]:
            self.state.show_chapter_list = True
        elif key in self.keybinds.get("help", []):
            self.state.show_help = True
        elif key in self.keybinds.get("bookmark_save", []):
            self._handle_save_bookmark()
        elif key in self.keybinds.get("bookmark_goto", []):
            self._handle_goto_bookmark()
        elif key in self.keybinds["next_page"]:
            self._handle_next_page(pages)
        elif key in self.keybinds["prev_page"]:
            self._handle_prev_page(pages, text_width, visible_height)
        elif key in self.keybinds["next_chapter"]:
            self.state.next_chapter()
        elif key in self.keybinds["prev_chapter"]:
            self.state.prev_chapter()
        elif key in self.keybinds["start"]:
            self.state.goto_start()
        elif key in self.keybinds["end"]:
            self.state.goto_end(text_width, visible_height)
        elif key in self.keybinds.get("toggle_double_page", []):
            self.state.toggle_double_page_mode()

        return True

    def _handle_save_bookmark(self) -> None:
        """Handle saving a bookmark."""
        if self.state.save_bookmark():
            self.state.notification = "Bookmark saved!"
        else:
            self.state.notification = "[red]Failed to save bookmark![/red]"

    def _handle_goto_bookmark(self) -> None:
        """Handle going to a saved bookmark."""
        if self.state.has_bookmark():
            if self.state.load_bookmark():
                self.state.notification = (
                    f"Jumped to bookmark: {self.state.get_bookmark_info()}"
                )
            else:
                self.state.notification = "[red]Failed to load bookmark![/red]"
        else:
            self.state.notification = (
                "[yellow]No bookmark found for this book![/yellow]"
            )

    def _handle_next_page(self, pages) -> None:
        """Handle next page navigation.

        Args:
            pages: Current chapter pages.
        """
        if not self.page_manager.next_page(pages):
            # At end of chapter, try to go to next chapter
            self.state.next_chapter()

    def _handle_prev_page(self, pages, text_width: int, visible_height: int) -> None:
        """Handle previous page navigation.

        Args:
            pages: Current chapter pages.
            text_width: Width for text wrapping.
            visible_height: Height for pagination.
        """
        self.page_manager.prev_page(pages, text_width, visible_height)


def display_book(epub_book) -> None:
    """Main entry point for displaying a book.

    Args:
        epub_book: EpubBook instance to display.
    """
    controller = UIController(epub_book)
    try:
        controller.run()
    finally:
        # Save auto-bookmark on exit
        controller.save_auto_bookmark()
