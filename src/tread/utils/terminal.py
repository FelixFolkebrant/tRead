"""Terminal utility functions for tRead."""

import sys
import tty
import termios
import os
from typing import Tuple


def get_terminal_size() -> Tuple[int, int]:
    try:
        width, height = os.get_terminal_size()
    except OSError:
        width, height = 80, 24  # Default fallback
    return width, height


def get_key() -> str:
    """Get a single keypress from the user.

    Returns:
        String representation of the pressed key(s).
        Arrow keys return escape sequences like '\x1b[A'.
    """
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
        if key == "\x1b":  # Handle arrow keys and other escape sequences
            key += sys.stdin.read(2)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key


def hide_cursor() -> None:
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor() -> None:
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


class CursorManager:
    def __enter__(self):
        hide_cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        show_cursor()
