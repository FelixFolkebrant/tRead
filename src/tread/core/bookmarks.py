"""Bookmark management for tRead."""

import json
import os
from typing import Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class Bookmark:
    """Represents a bookmark with chapter and page position."""

    chapter: int
    page: int
    timestamp: str
    title: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert bookmark to dictionary for JSON serialization."""
        return {
            "chapter": self.chapter,
            "page": self.page,
            "timestamp": self.timestamp,
            "title": self.title,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Bookmark":
        """Create bookmark from dictionary."""
        return cls(
            chapter=data["chapter"],
            page=data["page"],
            timestamp=data["timestamp"],
            title=data.get("title", ""),
        )


class BookmarkManager:
    """Manages bookmarks for EPUB books."""

    def __init__(self, bookmarks_dir: str = None):
        """Initialize bookmark manager.

        Args:
            bookmarks_dir: Directory to store bookmark files. Defaults to 'bookmarks'.
        """
        if bookmarks_dir is None:
            # Create bookmarks directory in the project root
            self.bookmarks_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "bookmarks"
            )
        else:
            self.bookmarks_dir = bookmarks_dir

        self.bookmarks_dir = os.path.abspath(self.bookmarks_dir)
        os.makedirs(self.bookmarks_dir, exist_ok=True)

    def _get_bookmark_file(self, book_title: str) -> str:
        """Get bookmark file path for a book.

        Args:
            book_title: Title of the book.

        Returns:
            Path to the bookmark file.
        """
        # Sanitize filename
        safe_title = "".join(
            c for c in book_title if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        safe_title = safe_title.replace(" ", "_")
        return os.path.join(self.bookmarks_dir, f"{safe_title}.json")

    def save_bookmark(self, book_title: str, bookmark: Bookmark) -> bool:
        """Save a bookmark for a book.

        Args:
            book_title: Title of the book.
            bookmark: Bookmark to save.

        Returns:
            True if successful, False otherwise.
        """
        try:
            bookmark_file = self._get_bookmark_file(book_title)
            bookmarks_data = self._load_bookmarks_data(book_title)

            # Save as the main bookmark (overwrite existing)
            bookmarks_data["current"] = bookmark.to_dict()

            with open(bookmark_file, "w", encoding="utf-8") as f:
                json.dump(bookmarks_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving bookmark: {e}")
            return False

    def load_bookmark(self, book_title: str) -> Optional[Bookmark]:
        """Load the current bookmark for a book.

        Args:
            book_title: Title of the book.

        Returns:
            Bookmark if exists, None otherwise.
        """
        try:
            bookmarks_data = self._load_bookmarks_data(book_title)
            if "current" in bookmarks_data:
                return Bookmark.from_dict(bookmarks_data["current"])
            return None
        except Exception as e:
            print(f"Error loading bookmark: {e}")
            return None

    def _load_bookmarks_data(self, book_title: str) -> Dict[str, Any]:
        """Load bookmarks data from file.

        Args:
            book_title: Title of the book.

        Returns:
            Dictionary containing bookmarks data.
        """
        bookmark_file = self._get_bookmark_file(book_title)
        if os.path.exists(bookmark_file):
            try:
                with open(bookmark_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def has_bookmark(self, book_title: str) -> bool:
        """Check if a book has a saved bookmark.

        Args:
            book_title: Title of the book.

        Returns:
            True if bookmark exists, False otherwise.
        """
        return self.load_bookmark(book_title) is not None

    def delete_bookmark(self, book_title: str) -> bool:
        """Delete the bookmark for a book.

        Args:
            book_title: Title of the book.

        Returns:
            True if successful, False otherwise.
        """
        try:
            bookmark_file = self._get_bookmark_file(book_title)
            if os.path.exists(bookmark_file):
                bookmarks_data = self._load_bookmarks_data(book_title)
                if "current" in bookmarks_data:
                    del bookmarks_data["current"]
                    if bookmarks_data:  # If there's other data, save it
                        with open(bookmark_file, "w", encoding="utf-8") as f:
                            json.dump(bookmarks_data, f, indent=2)
                    else:  # If file is empty, delete it
                        os.remove(bookmark_file)
            return True
        except Exception as e:
            print(f"Error deleting bookmark: {e}")
            return False
