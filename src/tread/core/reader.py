"""EPUB reader module for tRead."""

from ebooklib import epub
from ebooklib import ITEM_DOCUMENT
from bs4 import BeautifulSoup
import re
from typing import Dict, List
from .config import get_config


class EpubBook:
    """Represents an EPUB book with parsed chapters and metadata."""

    def __init__(self, filepath: str):
        self.book = epub.read_epub(filepath)
        self.chapters: List[Dict[str, str]] = []
        self.metadata: Dict[str, str] = {}
        self.formatting_config = get_config().formatting
        self._extract_metadata()
        self._extract_chapters()

    def _extract_metadata(self) -> None:
        self.metadata = {
            "title": self._get_metadata_field("title", "Unknown Title"),
            "author": self._get_metadata_field("creator", "Unknown Author"),
            "language": self._get_metadata_field("language", "Unknown"),
            "publisher": self._get_metadata_field("publisher", "Unknown"),
        }

    def _get_metadata_field(self, field_name: str, default: str) -> str:
        metadata = self.book.get_metadata("DC", field_name)
        return metadata[0][0] if metadata else default

    def _extract_chapters(self) -> None:
        spine_items = [
            item for item in self.book.get_items() if item.get_type() == ITEM_DOCUMENT
        ]

        for item in spine_items:
            soup = BeautifulSoup(item.get_content(), "html.parser")
            chapter_title = self._extract_chapter_title(soup, len(self.chapters) + 1)
            content = self._format_html_content(soup)

            if content.strip():  # Only add non-empty chapters
                self.chapters.append(
                    {"title": chapter_title, "content": content, "id": item.get_id()}
                )

    def _extract_chapter_title(self, soup: BeautifulSoup, chapter_number: int) -> str:
        title_tags = soup.find_all(["h1", "h2", "h3", "title"])
        if title_tags:
            return title_tags[0].get_text().strip()
        return f"Chapter {chapter_number}"

    def _format_html_content(self, soup: BeautifulSoup) -> str:
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        content = []
        for element in soup.find_all(
            ["p", "h1", "h2", "h3", "h4", "h5", "h6", "div", "br", "blockquote"]
        ):
            self._process_html_element(element, content)

        # If no structured content found, fall back to text extraction
        if not content:
            content = self._extract_fallback_content(soup)

        return "\n".join([line for line in content if line is not None])

    def _process_html_element(self, element, content: List[str]) -> None:
        paragraph_spacing = self.formatting_config.get("paragraph_spacing", 1)
        paragraph_indent = self.formatting_config.get("paragraph_indent", 0)

        # Skip title tags to avoid duplicate content
        if element.name == "title":
            return

        if element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self._process_header_element(element, content, paragraph_spacing)
        elif element.name == "p":
            self._process_paragraph_element(
                element, content, paragraph_spacing, paragraph_indent
            )
        elif element.name == "blockquote":
            self._process_blockquote_element(
                element, content, paragraph_spacing, paragraph_indent
            )
        elif element.name == "br":
            self._process_break_element(content)
        elif element.name == "div":
            self._process_div_element(
                element, content, paragraph_spacing, paragraph_indent
            )

    def _process_header_element(
        self, element, content: List[str], paragraph_spacing: int
    ) -> None:
        text = element.get_text().strip()
        if text:
            if content:  # Add spacing before header only if there's content before
                for _ in range(paragraph_spacing):
                    content.append("")
            content.append(f"[bold]{text}[/bold]")
            for _ in range(paragraph_spacing):
                content.append("")

    def _process_paragraph_element(
        self,
        element,
        content: List[str],
        paragraph_spacing: int,
        paragraph_indent: int,
    ) -> None:
        """Process paragraph elements.

        Args:
            element: Paragraph element to process.
            content: Content list to append to.
            paragraph_spacing: Number of empty lines to add after.
            paragraph_indent: Number of spaces to indent paragraphs.
        """
        text = self._format_inline_elements(element)
        if text.strip():
            text = self._apply_paragraph_indentation(text, element, paragraph_indent)
            content.append(text)
            for _ in range(paragraph_spacing):
                content.append("")

    def _process_blockquote_element(
        self,
        element,
        content: List[str],
        paragraph_spacing: int,
        paragraph_indent: int,
    ) -> None:
        text = self._format_inline_elements(element)
        if text.strip():
            base_indent = "    "
            if paragraph_indent > 0:
                base_indent = " " * (paragraph_indent + 4)
            indented_text = base_indent + text.replace("\n", "\n" + base_indent)
            content.append(f"[italic]{indented_text}[/italic]")
            for _ in range(paragraph_spacing):
                content.append("")

    def _process_break_element(self, content: List[str]) -> None:
        preserve_line_breaks = self.formatting_config.get("preserve_line_breaks", True)
        if preserve_line_breaks and content and content[-1] != "":
            content.append("")

    def _process_div_element(
        self, element, content: List[str], paragraph_spacing: int, paragraph_indent: int
    ) -> None:
        text = self._format_inline_elements(element)
        if text.strip():
            if paragraph_indent > 0:
                indent = " " * paragraph_indent
                text = indent + text.lstrip()
            content.append(text)
            for _ in range(paragraph_spacing):
                content.append("")

    def _apply_paragraph_indentation(
        self, text: str, element, paragraph_indent: int
    ) -> str:
        if paragraph_indent > 0:
            indent = " " * paragraph_indent
            return indent + text.lstrip()
        return text

    def _format_inline_elements(self, element) -> str:
        from bs4 import NavigableString, Tag

        # If element is a NavigableString, just return it
        if isinstance(element, NavigableString):
            return str(element)

        # Process Tag elements
        text_parts = []
        for content in getattr(element, "contents", []):
            if isinstance(content, Tag):
                text_parts.append(self._process_inline_tag(content))
            elif isinstance(content, NavigableString):
                text_parts.append(str(content))

        result = "".join(text_parts)
        return self._clean_whitespace(result)

    def _process_inline_tag(self, content) -> str:
        inner_text = self._format_inline_elements(content)

        if content.name in ["b", "strong"]:
            return f"[bold]{inner_text}[/bold]"
        elif content.name in ["i", "em"]:
            return f"[italic]{inner_text}[/italic]"
        elif content.name in ["u"]:
            return f"[underline]{inner_text}[/underline]"
        elif content.name in ["code", "tt"]:
            return f"`{inner_text}`"
        elif content.name in ["br"]:
            return "\n"
        else:
            # Recursively process other tags
            return inner_text

    def _clean_whitespace(self, result: str) -> str:
        return " ".join(result.split())  # Normalize all whitespace

    def _extract_fallback_content(self, soup: BeautifulSoup) -> List[str]:
        preserve_line_breaks = self.formatting_config.get("preserve_line_breaks", True)
        paragraph_indent = self.formatting_config.get("paragraph_indent", 0)
        paragraph_spacing = self.formatting_config.get("paragraph_spacing", 1)

        text = soup.get_text()

        if preserve_line_breaks:
            return self._process_text_with_line_breaks(
                text, paragraph_indent, paragraph_spacing
            )
        else:
            return self._process_text_simple(text, paragraph_indent, paragraph_spacing)

    def _process_text_with_line_breaks(
        self,
        text: str,
        paragraph_indent: int,
        paragraph_spacing: int,
    ) -> List[str]:
        lines = text.split("\n")
        processed_lines = []

        for line in lines:
            line = line.strip()
            if line:
                if paragraph_indent > 0:
                    processed_lines.append(" " * paragraph_indent + line)
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append("")

        # Group into paragraphs with configurable spacing
        final_content = []
        i = 0
        while i < len(processed_lines):
            if processed_lines[i]:  # Non-empty line
                final_content.append(processed_lines[i])
                # Skip empty lines and add configurable spacing
                i += 1
                while i < len(processed_lines) and not processed_lines[i]:
                    i += 1
                # Add spacing after paragraph
                for _ in range(paragraph_spacing):
                    final_content.append("")
            else:
                i += 1
        return final_content

    def _process_text_simple(
        self, text: str, paragraph_indent: int, paragraph_spacing: int
    ) -> List[str]:
        # Normalize whitespace
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        paragraphs = text.split("\n\n")

        content = []
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                paragraph = " ".join(paragraph.split())
                if paragraph_indent > 0:
                    paragraph = " " * paragraph_indent + paragraph
                content.append(paragraph)
                for _ in range(paragraph_spacing):
                    content.append("")
        return content


def load_book(filepath: str) -> EpubBook:
    return EpubBook(filepath)
