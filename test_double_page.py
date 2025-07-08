#!/usr/bin/env python3
"""Test script for double page functionality."""

from src.tread.utils.text import (
    create_pages,
    create_double_pages_with_width,
    wrap_text_to_width,
)


def test_double_page():
    # Sample text
    sample_text = """This is a test paragraph with some content.
    
Another paragraph here with different content.

And yet another paragraph to test the pagination.

This should demonstrate how double page mode works.

Each page will be displayed side by side like in a real book.

The left page shows the first content.

And the right page shows the next content.

This creates a more natural reading experience.

Especially for users who prefer book-like layouts.

You can toggle between single and double page modes.

Press 'd' to switch between the two modes.

The separator character helps distinguish the pages.

This is the end of our test content."""

    # Test parameters
    text_width = 80
    visible_height = 10

    print("=== Testing Single Page Mode ===")
    lines = wrap_text_to_width(sample_text, text_width)
    single_pages = create_pages(lines, visible_height)

    print(f"Single pages created: {len(single_pages)}")
    for i, page in enumerate(single_pages[:3]):  # Show first 3 pages
        print(f"\n--- Single Page {i+1} ---")
        for line in page:
            print(repr(line))

    print("\n=== Testing Double Page Mode ===")
    double_pages = create_double_pages_with_width(single_pages, text_width, " │ ")

    print(f"Double pages created: {len(double_pages)}")
    for i, page in enumerate(double_pages[:2]):  # Show first 2 double pages
        print(f"\n--- Double Page {i+1} ---")
        for line in page:
            print(repr(line))


if __name__ == "__main__":
    test_double_page()
