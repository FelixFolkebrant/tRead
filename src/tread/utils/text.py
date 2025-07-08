"""Text formatting and pagination utilities for tRead."""

import textwrap
from typing import List


def wrap_text_to_width(text: str, width: int) -> List[str]:
    """
    Args:
        text: The text to wrap.
        width: Maximum width in characters.

    Returns:
        List of wrapped lines.
    """
    wrapped_lines = []
    for line in text.split("\n"):
        if line.strip():  # Non-empty line
            wrapped_lines.extend(textwrap.wrap(line, width) or [""])
        else:  # Empty line (preserve spacing)
            wrapped_lines.append("")
    return wrapped_lines


def create_pages(lines: List[str], visible_height: int) -> List[List[str]]:
    """Group lines into pages that respect paragraph boundaries.

    Args:
        lines: List of text lines to paginate.
        visible_height: Number of lines that fit on one page.

    Returns:
        List of pages, where each page is a list of lines.
    """
    pages = []
    current_page = []

    i = 0
    while i < len(lines):
        # Add lines to current page until we reach capacity
        while len(current_page) < visible_height and i < len(lines):
            current_page.append(lines[i])
            i += 1

        # If we're at capacity but not at a paragraph break, try to find one
        if len(current_page) == visible_height and i < len(lines):
            # Look backwards for a good breaking point (empty line = paragraph end)
            for j in range(len(current_page) - 1, max(0, len(current_page) - 5), -1):
                if current_page[j] == "":  # Found empty line (paragraph break)
                    # Split here: keep everything up to and including the empty line
                    page_content = current_page[: j + 1]
                    remaining = current_page[j + 1 :]

                    # Fill rest of page with empty lines
                    while len(page_content) < visible_height:
                        page_content.append("")

                    pages.append(page_content)

                    # Put the remaining lines back for next page
                    i = i - len(remaining)
                    current_page = []
                    break
            else:
                # No good break found, just use the full page
                pages.append(current_page[:])
                current_page = []
        else:
            # Page isn't full or we're at the end
            if current_page:
                # Fill remaining space with empty lines
                while len(current_page) < visible_height:
                    current_page.append("")
                pages.append(current_page[:])
                current_page = []

    return pages
