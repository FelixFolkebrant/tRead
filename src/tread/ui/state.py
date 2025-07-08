"""UI state management and display logic for tRead."""

from typing import Dict, Tuple, List
from datetime import datetime

from ..utils.terminal import get_terminal_size
from ..utils.text import (
    wrap_text_to_width,
    create_pages,
    create_double_pages_with_width,
)
from ..core.bookmarks import BookmarkManager, Bookmark
from ..core.config import get_config


class ReadingState:
    """Manages the current reading state including chapter and page position."""

    def __init__(self, epub_book):
        self.epub_book = epub_book
        self.current_chapter = 0
        self.current_page = 0
        self.show_chapter_list = False
        self.show_help = False
        self.bookmark_manager = BookmarkManager()
        self.notification = None  # For UI notifications (e.g., bookmark saved)
        self.double_page_mode = get_config().reading.get("double_page_mode", False)

    def is_valid_chapter(self, chapter_index: int) -> bool:
        return 0 <= chapter_index < len(self.epub_book.chapters)

    def get_current_chapter(self) -> Dict[str, str]:
        if self.is_valid_chapter(self.current_chapter):
            return self.epub_book.chapters[self.current_chapter]
        return {"title": "Unknown", "content": "", "id": ""}

    def navigate_to_chapter(self, chapter_index: int) -> None:
        if self.is_valid_chapter(chapter_index):
            self.current_chapter = chapter_index
            self.current_page = 0

    def next_chapter(self) -> bool:
        if self.current_chapter < len(self.epub_book.chapters) - 1:
            self.current_chapter += 1
            self.current_page = 0
            return True
        return False

    def prev_chapter(self) -> bool:
        if self.current_chapter > 0:
            self.current_chapter -= 1
            self.current_page = 0
            return True
        return False

    def goto_start(self) -> None:
        self.current_chapter = 0
        self.current_page = 0

    def goto_end(self, text_width: int, visible_height: int) -> None:
        from ..utils.terminal import get_terminal_size

        terminal_width, _ = get_terminal_size()
        self.current_chapter = len(self.epub_book.chapters) - 1
        chapter = self.get_current_chapter()
        double_page = self.effective_double_page_mode(terminal_width)
        if double_page:
            config = get_config()
            separator = config.reading.get("double_page_separator", " │ ")
            single_page_width = (text_width - len(separator)) // 2 - 2
            lines = wrap_text_to_width(chapter["content"], max(20, single_page_width))
        else:
            lines = wrap_text_to_width(chapter["content"], text_width)
        pages = create_pages(lines, visible_height)
        if double_page:
            config = get_config()
            separator = config.reading.get("double_page_separator", " │ ")
            pages = create_double_pages_with_width(pages, text_width, separator)
        self.current_page = len(pages) - 1 if pages else 0

    def save_bookmark(self) -> bool:
        """Save current reading position as a bookmark.

        Returns:
            True if successful, False otherwise.
        """
        try:
            chapter = self.get_current_chapter()
            bookmark = Bookmark(
                chapter=self.current_chapter,
                page=self.current_page,
                timestamp=datetime.now().isoformat(),
                title=chapter.get("title", f"Chapter {self.current_chapter + 1}"),
            )
            return self.bookmark_manager.save_bookmark(
                self.epub_book.metadata["title"], bookmark
            )
        except Exception as e:
            print(f"Error saving bookmark: {e}")
            return False

    def load_bookmark(self) -> bool:
        """Load saved bookmark and navigate to that position.

        Returns:
            True if bookmark was loaded, False if no bookmark exists.
        """
        try:
            bookmark = self.bookmark_manager.load_bookmark(
                self.epub_book.metadata["title"]
            )
            if bookmark:
                if self.is_valid_chapter(bookmark.chapter):
                    self.current_chapter = bookmark.chapter
                    self.current_page = bookmark.page
                    return True
            return False
        except Exception as e:
            print(f"Error loading bookmark: {e}")
            return False

    def has_bookmark(self) -> bool:
        """Check if the current book has a saved bookmark.

        Returns:
            True if bookmark exists, False otherwise.
        """
        return self.bookmark_manager.has_bookmark(self.epub_book.metadata["title"])

    def get_bookmark_info(self) -> str:
        """Get human-readable bookmark information.

        Returns:
            String describing the bookmark position.
        """
        try:
            bookmark = self.bookmark_manager.load_bookmark(
                self.epub_book.metadata["title"]
            )
            if bookmark:
                chapter = (
                    self.epub_book.chapters[bookmark.chapter]
                    if bookmark.chapter < len(self.epub_book.chapters)
                    else None
                )
                if chapter:
                    return f"Chapter {bookmark.chapter + 1}: {chapter['title']} (Page {bookmark.page + 1})"
                else:
                    return f"Chapter {bookmark.chapter + 1} (Page {bookmark.page + 1})"
            return "No bookmark found"
        except Exception:
            return "Error reading bookmark"

    def get_double_page_mode(self, terminal_width: int = None) -> bool:
        """Determine double page mode based on current breakpoint in config, using terminal width."""
        config = get_config()
        display = config.display
        breakpoints = display.get("breakpoints", {})
        if terminal_width is None:
            # Get current terminal width
            terminal_width, _ = get_terminal_size()
        # Find the matching breakpoint
        for bp in breakpoints.values():
            if terminal_width <= bp.get("max_width", 9999):
                return bp.get("double_page_mode", False)
        # Fallback
        return False

    def toggle_double_page_mode(self, terminal_width: int = None) -> None:
        """Toggle double page mode for the current breakpoint (overrides config for session)."""
        if not hasattr(self, "_double_page_override"):
            self._double_page_override = None
        current = self.get_double_page_mode(terminal_width)
        self._double_page_override = (
            not current
            if self._double_page_override is None
            else not self._double_page_override
        )
        mode_text = "double page" if self._double_page_override else "single page"
        self.notification = f"[blue]Switched to {mode_text} mode[/blue]"

    def effective_double_page_mode(self, terminal_width: int = None) -> bool:
        if (
            hasattr(self, "_double_page_override")
            and self._double_page_override is not None
        ):
            return self._double_page_override
        return self.get_double_page_mode(terminal_width)


class DisplayCalculator:
    # Configuration constants
    PANEL_BORDER = 4
    PANEL_PADDING_Y = 1
    PANEL_EXTRA_HEIGHT = 3
    PANEL_HEIGHT_OFFSET = 0

    @classmethod
    def _get_responsive_padding_x(cls, terminal_width: int) -> int:
        """Calculate responsive horizontal padding based on terminal width."""
        config = get_config()
        display_config = config.display

        # Check if responsive padding is enabled
        if not display_config.get("responsive_padding", True):
            return display_config.get("fallback_padding_x", 30)

        breakpoints = display_config.get("breakpoints", {})

        # Sort breakpoints by max_width to find the right one
        sorted_breakpoints = sorted(
            breakpoints.items(), key=lambda x: x[1].get("max_width", 0)
        )

        # Find the first breakpoint that accommodates our terminal width
        for name, breakpoint in sorted_breakpoints:
            if terminal_width <= breakpoint.get("max_width", 9999):
                return breakpoint.get("padding_x", 30)

        # Fallback if no breakpoint matches
        return display_config.get("fallback_padding_x", 30)

    @classmethod
    def get_display_dimensions(cls) -> Tuple[int, int, int, int]:
        width, height = get_terminal_size()

        # Use responsive padding
        padding_x = cls._get_responsive_padding_x(width)

        panel_width = width - cls.PANEL_BORDER
        text_width = panel_width - (padding_x * 2)
        visible_height = (
            height
            - cls.PANEL_EXTRA_HEIGHT
            - cls.PANEL_HEIGHT_OFFSET
            - cls.PANEL_PADDING_Y * 2
        )
        return panel_width, text_width, visible_height, height

    @classmethod
    def get_panel_padding_x(cls) -> int:
        """Get the current responsive horizontal padding value."""
        width, _ = get_terminal_size()
        return cls._get_responsive_padding_x(width)


class PageManager:
    def __init__(self, state: ReadingState):
        self.state = state

    def get_current_pages(
        self, text_width: int, visible_height: int
    ) -> Tuple[List[List[str]], Dict[str, int]]:
        from ..utils.terminal import get_terminal_size

        terminal_width, _ = get_terminal_size()
        chapter = self.state.get_current_chapter()
        double_page = self.state.effective_double_page_mode(terminal_width)
        if double_page:
            config = get_config()
            separator = config.reading.get("double_page_separator", " │ ")
            single_page_width = (text_width - len(separator)) // 2 - 2
            lines = wrap_text_to_width(chapter["content"], max(20, single_page_width))
        else:
            lines = wrap_text_to_width(chapter["content"], text_width)
        pages = create_pages(lines, visible_height)
        if double_page:
            config = get_config()
            separator = config.reading.get("double_page_separator", " │ ")
            pages = create_double_pages_with_width(pages, text_width, separator)
        self.state.current_page = max(0, min(self.state.current_page, len(pages) - 1))
        chapter_progress = (
            int((self.state.current_page / len(pages) * 100)) if pages else 0
        )
        total_chapters = len(self.state.epub_book.chapters)
        overall_progress = int(
            (
                (self.state.current_chapter / total_chapters)
                + (chapter_progress / 100 / total_chapters)
            )
            * 100
        )
        progress_info = {
            "chapter_progress": chapter_progress,
            "overall_progress": overall_progress,
            "total_chapters": total_chapters,
        }
        return pages, progress_info

    def next_page(self, pages: List[List[str]]) -> bool:
        """
        Move to next page.
        True if moved within chapter, False if need to change chapter.
        """
        if self.state.current_page < len(pages) - 1:
            self.state.current_page += 1
            return True
        return False

    def prev_page(
        self, pages: List[List[str]], text_width: int, visible_height: int
    ) -> bool:
        from ..utils.terminal import get_terminal_size

        terminal_width, _ = get_terminal_size()
        if self.state.current_page > 0:
            self.state.current_page -= 1
            return True
        elif self.state.current_chapter > 0:
            self.state.current_chapter -= 1
            prev_chapter = self.state.get_current_chapter()
            double_page = self.state.effective_double_page_mode(terminal_width)
            if double_page:
                config = get_config()
                separator = config.reading.get("double_page_separator", " │ ")
                single_page_width = (text_width - len(separator)) // 2 - 2
                prev_lines = wrap_text_to_width(
                    prev_chapter["content"], max(20, single_page_width)
                )
            else:
                prev_lines = wrap_text_to_width(prev_chapter["content"], text_width)
            prev_pages = create_pages(prev_lines, visible_height)
            if double_page:
                config = get_config()
                separator = config.reading.get("double_page_separator", " │ ")
                prev_pages = create_double_pages_with_width(
                    prev_pages, text_width, separator
                )
            self.state.current_page = len(prev_pages) - 1 if prev_pages else 0
            return True
        return False
