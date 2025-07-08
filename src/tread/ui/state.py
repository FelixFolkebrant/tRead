"""UI state management and display logic for tRead."""

from typing import Dict, Tuple, List
from datetime import datetime

from ..utils.terminal import get_terminal_size
from ..utils.text import wrap_text_to_width, create_pages
from ..core.bookmarks import BookmarkManager, Bookmark


class ReadingState:
    """Manages the current reading state including chapter and page position."""

    def __init__(self, epub_book):
        self.epub_book = epub_book
        self.current_chapter = 0
        self.current_page = 0
        self.show_chapter_list = False
        self.show_help = False
        self.bookmark_manager = BookmarkManager()

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
        self.current_chapter = len(self.epub_book.chapters) - 1
        chapter = self.get_current_chapter()
        lines = wrap_text_to_width(chapter["content"], text_width)
        pages = create_pages(lines, visible_height)
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


class DisplayCalculator:
    # Configuration constants
    PANEL_BORDER = 4
    PANEL_PADDING_Y = 1
    PANEL_PADDING_X = 30
    PANEL_EXTRA_HEIGHT = 3
    PANEL_HEIGHT_OFFSET = 0

    @classmethod
    def get_display_dimensions(cls) -> Tuple[int, int, int, int]:
        width, height = get_terminal_size()
        panel_width = width - cls.PANEL_BORDER
        text_width = panel_width - (cls.PANEL_PADDING_X * 2)
        visible_height = (
            height
            - cls.PANEL_EXTRA_HEIGHT
            - cls.PANEL_HEIGHT_OFFSET
            - cls.PANEL_PADDING_Y * 2
        )
        return panel_width, text_width, visible_height, height


class PageManager:
    def __init__(self, state: ReadingState):
        self.state = state

    def get_current_pages(
        self, text_width: int, visible_height: int
    ) -> Tuple[List[List[str]], Dict[str, int]]:
        """Get current pages and progress information.
        Args:
            text_width: Width for text wrapping.
            visible_height: Height for pagination.
        """
        chapter = self.state.get_current_chapter()
        lines = wrap_text_to_width(chapter["content"], text_width)
        pages = create_pages(lines, visible_height)

        # Ensure current page is within bounds
        self.state.current_page = max(0, min(self.state.current_page, len(pages) - 1))

        # Calculate progress
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
        if self.state.current_page > 0:
            self.state.current_page -= 1
            return True
        elif self.state.current_chapter > 0:
            # Move to last page of previous chapter
            self.state.current_chapter -= 1
            prev_chapter = self.state.get_current_chapter()
            prev_lines = wrap_text_to_width(prev_chapter["content"], text_width)
            prev_pages = create_pages(prev_lines, visible_height)
            self.state.current_page = len(prev_pages) - 1 if prev_pages else 0
            return True
        return False
