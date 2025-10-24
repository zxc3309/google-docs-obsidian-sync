"""
Document Converter Module

Handles conversion between Google Docs and Markdown formats
"""

import logging
import re
from markdownify import markdownify as md

logger = logging.getLogger(__name__)


class DocumentConverter:
    """Converter for Google Docs <-> Markdown"""

    @staticmethod
    def html_to_markdown(html_content: str) -> str:
        """
        Convert Google Docs HTML to Markdown

        Args:
            html_content: HTML content from Google Docs

        Returns:
            str: Markdown formatted content
        """
        try:
            # Pre-process: Remove style and script tags with content
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

            # Remove head section entirely
            html_content = re.sub(r'<head[^>]*>.*?</head>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

            # Reconstruct nested lists based on margin-left
            html_content = DocumentConverter._reconstruct_nested_lists(html_content)

            # Convert HTML to Markdown
            markdown = md(
                html_content,
                heading_style="ATX",  # Use # for headings
                bullets="-",  # Use - for unordered lists
                strong_em_symbol="**",  # Use ** for bold
                strip=['style', 'script']  # Remove style and script tags
            )

            # Keep tabs for nested lists (Obsidian uses tabs for list indentation)
            # Do NOT convert tabs to spaces

            # Clean up extra whitespace
            markdown = re.sub(r'\n{3,}', '\n\n', markdown)  # Max 2 consecutive newlines
            markdown = markdown.strip()

            # Remove trailing spaces from each line (important for proper list rendering)
            markdown = re.sub(r' +$', '', markdown, flags=re.MULTILINE)

            # Remove Google Docs specific artifacts
            markdown = DocumentConverter._clean_google_docs_artifacts(markdown)

            logger.info("Converted HTML to Markdown")
            return markdown

        except Exception as e:
            logger.error(f"Error converting HTML to Markdown: {e}")
            raise

    @staticmethod
    def _reconstruct_nested_lists(html: str) -> str:
        """
        Reconstruct nested list structure based on margin-left values

        Google Docs exports lists as separate <ul> blocks with margin-left
        indicating the nesting level. This function reconstructs proper
        nested <ul> structure.

        Args:
            html: HTML content with Google Docs list structure

        Returns:
            str: HTML with reconstructed nested lists
        """
        from html.parser import HTMLParser

        class ListItem:
            def __init__(self, level, content):
                self.level = level
                self.content = content
                self.children = []

        class GoogleListParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.items = []
                self.current_item = None
                self.in_li = False
                self.li_content = []

            def handle_starttag(self, tag, attrs):
                if tag == 'li':
                    self.in_li = True
                    self.li_content = []
                    # Extract margin-left from style attribute
                    style = dict(attrs).get('style', '')
                    margin_match = re.search(r'margin-left:\s*(\d+)pt', style)
                    if margin_match:
                        margin = int(margin_match.group(1))
                        # Calculate level: each 36pt is one level
                        level = max(0, (margin // 36) - 1)
                    else:
                        level = 0
                    self.current_item = ListItem(level, '')
                elif self.in_li:
                    # Reconstruct tag for content
                    attrs_str = ' '.join([f'{k}="{v}"' for k, v in attrs])
                    self.li_content.append(f'<{tag} {attrs_str}>' if attrs_str else f'<{tag}>')

            def handle_endtag(self, tag):
                if tag == 'li' and self.in_li:
                    self.current_item.content = ''.join(self.li_content)
                    self.items.append(self.current_item)
                    self.in_li = False
                    self.current_item = None
                elif self.in_li:
                    self.li_content.append(f'</{tag}>')

            def handle_data(self, data):
                if self.in_li:
                    self.li_content.append(data)

        # Build nested structure from a list of items
        def build_nested_html(items):
            if not items:
                return ''

            html_parts = []
            i = 0
            while i < len(items):
                item = items[i]
                html_parts.append(f'<li>{item.content}')

                # Check if next items are children (higher level)
                j = i + 1
                while j < len(items) and items[j].level > item.level:
                    j += 1

                if j > i + 1:
                    # Has children
                    children = items[i+1:j]
                    html_parts.append('<ul>')
                    html_parts.append(build_nested_html(children))
                    html_parts.append('</ul>')
                    i = j
                else:
                    i += 1

                html_parts.append('</li>')

            return ''.join(html_parts)

        # Process each <ul> block separately to preserve content between lists
        def process_one_list(match):
            ul_content = match.group(0)

            # Parse this specific <ul> block
            local_parser = GoogleListParser()
            try:
                local_parser.feed(ul_content)
            except:
                return ul_content

            if not local_parser.items:
                return ul_content

            # Rebuild with proper nesting
            return f'<ul>{build_nested_html(local_parser.items)}</ul>'

        # Replace each <ul>...</ul> block independently
        html = re.sub(r'<ul[^>]*>.*?</ul>', process_one_list, html, flags=re.DOTALL)

        return html

    @staticmethod
    def _clean_google_docs_artifacts(markdown: str) -> str:
        """
        Clean Google Docs specific artifacts from markdown

        Args:
            markdown: Markdown content

        Returns:
            str: Cleaned markdown
        """
        # Remove empty links
        markdown = re.sub(r'\[\]\(.*?\)', '', markdown)

        # Clean up excessive spacing in lists
        markdown = re.sub(r'(\n-\s+)\n+', r'\1', markdown)

        # Remove zero-width spaces and other invisible characters
        markdown = markdown.replace('\u200b', '')  # Zero-width space
        markdown = markdown.replace('\ufeff', '')  # Zero-width no-break space

        return markdown

    @staticmethod
    def markdown_to_plain_text(markdown_content: str) -> str:
        """
        Convert Markdown to plain text (for updating Google Docs)

        This is a simple conversion that removes markdown formatting
        but preserves the text structure.

        Args:
            markdown_content: Markdown formatted content

        Returns:
            str: Plain text content
        """
        try:
            text = markdown_content

            # Remove code blocks
            text = re.sub(r'```[\s\S]*?```', '', text)
            text = re.sub(r'`([^`]+)`', r'\1', text)

            # Convert headers to plain text (keep the text, add newlines)
            text = re.sub(r'^#{1,6}\s+(.+)$', r'\1\n', text, flags=re.MULTILINE)

            # Convert bold and italic
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
            text = re.sub(r'\*(.+?)\*', r'\1', text)
            text = re.sub(r'__(.+?)__', r'\1', text)
            text = re.sub(r'_(.+?)_', r'\1', text)

            # Convert links [text](url) to just text
            text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

            # Convert lists while preserving indentation
            # Convert tabs to 4 spaces for Google Docs compatibility
            text = text.replace('\t', '    ')
            # Remove list markers but keep indentation
            text = re.sub(r'^(\s*)[-*+]\s+', r'\1', text, flags=re.MULTILINE)
            text = re.sub(r'^(\s*)\d+\.\s+', r'\1', text, flags=re.MULTILINE)

            # Clean up extra whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = text.strip()

            logger.info("Converted Markdown to plain text")
            return text

        except Exception as e:
            logger.error(f"Error converting Markdown to plain text: {e}")
            raise

    @staticmethod
    def preserve_obsidian_links(markdown: str) -> str:
        """
        Ensure Obsidian-style links are preserved

        Args:
            markdown: Markdown content

        Returns:
            str: Markdown with preserved Obsidian links
        """
        # Obsidian uses [[link]] format for internal links
        # This function ensures they're not corrupted during conversion
        # For now, this is a placeholder - markdownify should preserve them

        return markdown

    @staticmethod
    def add_frontmatter(markdown: str, metadata: dict = None) -> str:
        """
        Add YAML frontmatter to markdown (optional)

        Args:
            markdown: Markdown content
            metadata: Dictionary of metadata to add

        Returns:
            str: Markdown with frontmatter
        """
        if not metadata:
            return markdown

        frontmatter_lines = ['---']
        for key, value in metadata.items():
            frontmatter_lines.append(f'{key}: {value}')
        frontmatter_lines.append('---')
        frontmatter_lines.append('')

        return '\n'.join(frontmatter_lines) + markdown

    @staticmethod
    def extract_frontmatter(markdown: str) -> tuple:
        """
        Extract YAML frontmatter from markdown

        Args:
            markdown: Markdown content with potential frontmatter

        Returns:
            tuple: (metadata dict, content without frontmatter)
        """
        # Simple frontmatter extraction
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, markdown, re.DOTALL)

        if match:
            frontmatter_text = match.group(1)
            content = markdown[match.end():]

            # Parse frontmatter (simple key: value format)
            metadata = {}
            for line in frontmatter_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()

            return metadata, content
        else:
            return {}, markdown
