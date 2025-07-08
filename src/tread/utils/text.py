"""Text formatting and pagination utilities for tRead."""

import textwrap
import re
from typing import List, Tuple


def parse_markup_tags(line: str) -> Tuple[List[str], List[str]]:
    """Parse Rich markup tags from a line.

    Args:
        line: Line of text potentially containing Rich markup tags.

    Returns:
        Tuple of (opening_tags, closing_tags) found in the line.
    """
    # Pattern to match Rich markup tags
    tag_pattern = r"\[/?([a-zA-Z0-9_]+(?:\s+[^]]*)?)\]"

    opening_tags = []
    closing_tags = []

    for match in re.finditer(tag_pattern, line):
        tag = match.group(0)
        if tag.startswith("[/"):
            # Closing tag
            tag_name = tag[2:-1]  # Remove [/ and ]
            closing_tags.append(tag_name)
        else:
            # Opening tag
            tag_name = tag[1:-1]  # Remove [ and ]
            # Handle tags with attributes (like "bold red")
            tag_name = tag_name.split()[0] if " " in tag_name else tag_name
            opening_tags.append(tag_name)

    return opening_tags, closing_tags


def track_open_tags(lines: List[str]) -> List[str]:
    """Track which markup tags are open at the end of a list of lines.

    Args:
        lines: List of text lines with potential markup.

    Returns:
        List of tag names that are currently open.
    """
    open_tags = []

    for line in lines:
        opening, closing = parse_markup_tags(line)

        # Add opening tags
        open_tags.extend(opening)

        # Remove closing tags (in reverse order)
        for tag in closing:
            if tag in open_tags:
                # Remove the most recent occurrence
                for i in range(len(open_tags) - 1, -1, -1):
                    if open_tags[i] == tag:
                        open_tags.pop(i)
                        break

    return open_tags


def close_open_tags(open_tags: List[str]) -> str:
    """Generate closing tags for all open tags.

    Args:
        open_tags: List of tag names that are currently open.

    Returns:
        String with closing tags in reverse order.
    """
    if not open_tags:
        return ""

    # Close tags in reverse order (LIFO)
    closing_tags = [f"[/{tag}]" for tag in reversed(open_tags)]
    return "".join(closing_tags)


def open_tags_string(open_tags: List[str]) -> str:
    """Generate opening tags for a list of tag names.

    Args:
        open_tags: List of tag names to open.

    Returns:
        String with opening tags.
    """
    if not open_tags:
        return ""

    opening_tags = [f"[{tag}]" for tag in open_tags]
    return "".join(opening_tags)


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
    """Group lines into pages that respect paragraph boundaries and preserve markup continuity.

    Args:
        lines: List of text lines to paginate.
        visible_height: Number of lines that fit on one page.

    Returns:
        List of pages, where each page is a list of lines with balanced markup tags.
    """
    pages = []
    current_page = []
    current_open_tags = []  # Track tags open at start of current page

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

                    # Handle markup continuity
                    page_content = _finalize_page_markup(
                        page_content, current_open_tags
                    )

                    # Track open tags for next page
                    current_open_tags = track_open_tags(
                        [open_tags_string(current_open_tags)] + page_content
                    )

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
                page_content = _finalize_page_markup(current_page[:], current_open_tags)
                current_open_tags = track_open_tags(
                    [open_tags_string(current_open_tags)] + current_page
                )
                pages.append(page_content)
                current_page = []
        else:
            # Page isn't full or we're at the end
            if current_page:
                page_content = _finalize_page_markup(current_page[:], current_open_tags)

                # Fill remaining space with empty lines
                while len(page_content) < visible_height:
                    page_content.append("")

                pages.append(page_content)
                current_page = []

    return pages


def _finalize_page_markup(
    page_content: List[str], start_open_tags: List[str]
) -> List[str]:
    """Finalize a page by ensuring markup tags are balanced.

    Args:
        page_content: List of lines for this page.
        start_open_tags: Tags that were open at the start of this page.

    Returns:
        Page content with balanced markup tags.
    """
    if not page_content:
        return page_content

    # If we have tags open from previous page, prepend them to first non-empty line
    if start_open_tags:
        for i, line in enumerate(page_content):
            if line.strip():  # First non-empty line
                page_content[i] = open_tags_string(start_open_tags) + line
                break

    # Track all open tags at the end of this page
    all_open_tags = track_open_tags([open_tags_string(start_open_tags)] + page_content)

    # If there are open tags at the end, close them on the last non-empty line
    if all_open_tags:
        for i in range(len(page_content) - 1, -1, -1):
            if page_content[i].strip():  # Last non-empty line
                page_content[i] = page_content[i] + close_open_tags(all_open_tags)
                break

    return page_content


def create_double_pages(
    pages: List[List[str]], separator: str = " │ "
) -> List[List[str]]:
    """Convert single pages to double pages for side-by-side reading.

    Args:
        pages: List of single pages.
        separator: String to separate left and right pages.

    Returns:
        List of double pages, where each double page combines two single pages side by side.
    """
    if not pages:
        return []

    double_pages = []

    # Process pages in pairs
    for i in range(0, len(pages), 2):
        left_page = pages[i]
        right_page = pages[i + 1] if i + 1 < len(pages) else [""] * len(left_page)

        # Ensure both pages have the same height
        max_height = max(len(left_page), len(right_page))
        while len(left_page) < max_height:
            left_page.append("")
        while len(right_page) < max_height:
            right_page.append("")

        # Calculate column width for each page (accounting for separator)
        # We'll make each column roughly half the available width
        combined_page = []
        for j in range(max_height):
            left_line = left_page[j] if j < len(left_page) else ""
            right_line = right_page[j] if j < len(right_page) else ""
            combined_line = left_line + separator + right_line
            combined_page.append(combined_line)

        double_pages.append(combined_page)

    return double_pages


def create_double_pages_with_width(
    pages: List[List[str]], total_width: int, separator: str = " │ "
) -> List[List[str]]:
    """Convert single pages to double pages with proper width management.

    Args:
        pages: List of single pages.
        total_width: Total available width for the double page display.
        separator: String to separate left and right pages.

    Returns:
        List of double pages properly formatted for the given width.
    """
    if not pages:
        return []

    # Calculate width for each column
    separator_width = len(separator)
    column_width = (total_width - separator_width) // 2

    double_pages = []

    # Process pages in pairs
    for i in range(0, len(pages), 2):
        left_page = pages[i]
        right_page = pages[i + 1] if i + 1 < len(pages) else [""] * len(left_page)

        # Ensure both pages have the same height
        max_height = max(len(left_page), len(right_page))
        while len(left_page) < max_height:
            left_page.append("")
        while len(right_page) < max_height:
            right_page.append("")

        # Format each line to fit within column width
        combined_page = []
        for j in range(max_height):
            left_line = left_page[j] if j < len(left_page) else ""
            right_line = right_page[j] if j < len(right_page) else ""

            # Clean and format lines to fit column width
            left_formatted = _format_line_for_column(left_line, column_width)
            right_formatted = _format_line_for_column(right_line, column_width)

            combined_line = left_formatted + separator + right_formatted
            combined_page.append(combined_line)

        double_pages.append(combined_page)

    return double_pages


def _format_line_for_column(line: str, column_width: int) -> str:
    """Format a line to fit within a specific column width, handling markup properly.

    Args:
        line: The line to format.
        column_width: Maximum width for the column.

    Returns:
        Formatted line that fits within the column width.
    """
    if not line.strip():
        # Empty line - just pad to column width
        return " " * column_width

    # For lines with content, we need to handle Rich markup carefully
    # First, let's get the visible length (without markup)
    import re

    # Remove Rich markup to calculate visible length
    visible_text = re.sub(r"\[/?[^\]]*\]", "", line)
    visible_length = len(visible_text)

    if visible_length <= column_width:
        # Line fits, pad with spaces to column width
        padding_needed = column_width - visible_length
        return line + (" " * padding_needed)
    else:
        # Line is too long, we need to truncate it
        # This is tricky with markup, so for now we'll do a simple truncation
        # TODO: Implement proper markup-aware truncation
        return line[:column_width]


def sanitize_markup(text: str) -> str:
    """Sanitize text to prevent Rich markup errors by balancing tags.

    Args:
        text: Text that might contain unbalanced Rich markup tags.

    Returns:
        Text with balanced markup tags.
    """
    import re

    # Find all markup tags
    tag_pattern = r"\[/?([a-zA-Z0-9_]+(?:\s+[^\]]*)?)\]"

    # Track open tags
    open_tags = []
    result_lines = []

    for line in text.split("\n"):
        # Find all tags in this line
        matches = list(re.finditer(tag_pattern, line))

        for match in matches:
            tag = match.group(0)
            if tag.startswith("[/"):
                # Closing tag
                tag_name = tag[2:-1]
                if tag_name in open_tags:
                    open_tags.remove(tag_name)
                else:
                    # Unmatched closing tag - remove it
                    line = line.replace(tag, "", 1)
            else:
                # Opening tag
                tag_name = tag[1:-1].split()[0] if " " in tag[1:-1] else tag[1:-1]
                open_tags.append(tag_name)

        result_lines.append(line)

    # Close any remaining open tags at the end
    if open_tags:
        closing_tags = "".join(f"[/{tag}]" for tag in reversed(open_tags))
        if result_lines:
            result_lines[-1] += closing_tags

    return "\n".join(result_lines)
