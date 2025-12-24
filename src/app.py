import json
import re
from typing import List, Dict, Any

class AdvancedPDFHeadingExtractor:
    def __init__(self, pdf_text: str):
        self.pdf_text = pdf_text
        self.lines = [line.strip() for line in pdf_text.split('\n') if line.strip()]
        self.current_page = 1

    def extract_headings(self) -> Dict[str, Any]:
        self._parse_page_info()

        headings = []

        headings.extend(self._extract_numbered_headings())
        headings.extend(self._extract_structural_headings())
        headings.extend(self._extract_toc_headings())

        cleaned_headings = self._clean_and_process_headings(headings)
        title = self._determine_document_title(cleaned_headings)

        return {
            "title": title,
            "outline": cleaned_headings
        }

    def _parse_page_info(self):
        self.line_to_page = {}
        current_page = 1

        for i, line in enumerate(self.lines):
            page_match = re.search(r'Page (\d+) of (\d+)', line)
            if page_match:
                current_page = int(page_match.group(1))

            self.line_to_page[i] = current_page

    def _extract_numbered_headings(self) -> List[Dict[str, Any]]:
        headings = []

        for i, line in enumerate(self.lines):
            if self._is_noise_line(line):
                continue

            # Match numbered headings like "1. Introduction"
            main_match = re.match(r'^(\d+)\.\s+(.+)$', line)
            if main_match:
                num = main_match.group(1)
                text = self._clean_heading_text(main_match.group(2))

                if self._is_valid_heading(text, i):
                    headings.append({
                        "level": "H1",
                        "text": f"{num}. {text}",
                        "page": self.line_to_page.get(i, 1),
                        "position": i,
                        "confidence": 0.9
                    })
                continue

            # Match sub-numbered headings like "1.1 Overview"
            sub_match = re.match(r'^(\d+\.\d+)\s+(.+)$', line)
            if sub_match:
                num = sub_match.group(1)
                text = self._clean_heading_text(sub_match.group(2))

                if self._is_valid_heading(text, i):
                    headings.append({
                        "level": "H2",
                        "text": f"{num} {text}",
                        "page": self.line_to_page.get(i, 1),
                        "position": i,
                        "confidence": 0.8
                    })

        return headings

    def _extract_structural_headings(self) -> List[Dict[str, Any]]:
        headings = []

        structural_patterns = {
            r'^(acknowledgements?)$': 'H1',
            r'^(abstract)$': 'H1',
            r'^(introduction)$': 'H1',
            r'^(conclusion)$': 'H1',
            r'^(references?)$': 'H1',
            r'^(revision\s+history)$': 'H1',
            r'^(table\s+of\s+contents?)$': 'H1',

            r'^(intended\s+audience)$': 'H2',
            r'^(career\s+paths?.*)$': 'H2',
            r'^(learning\s+objectives?)$': 'H2',
            r'^(entry\s+requirements?)$': 'H2',
            r'^(business\s+outcomes?)$': 'H2',
            r'^(content)$': 'H2',
            r'^(trademarks?)$': 'H2',
        }

        for i, line in enumerate(self.lines):
            line_lower = line.lower().strip()

            for pattern, level in structural_patterns.items():
                if re.match(pattern, line_lower):
                    if self._is_valid_heading(line, i):
                        headings.append({
                            "level": level,
                            "text": line,
                            "page": self.line_to_page.get(i, 1),
                            "position": i,
                            "confidence": 0.6
                        })
                        break

        return headings

    def _extract_toc_headings(self) -> List[Dict[str, Any]]:
        headings = []
        in_toc = False

        for i, line in enumerate(self.lines):
            line_lower = line.lower().strip()

            if 'table of contents' in line_lower:
                in_toc = True
                continue

            # Exit TOC when we hit a new section or page
            if in_toc and (line_lower.startswith('page ') or
                          line_lower in ['abstract', 'introduction', 'acknowledgements']):
                in_toc = False
                continue

            if in_toc and line:
                patterns = [
                    r'^(\d+)\.\s+(.+?)\s+(\d+)$',  # "1. Introduction 5"
                    r'^(\d+\.\d+)\s+(.+?)\s+(\d+)$',  # "1.1 Overview 7"
                ]

                for pattern in patterns:
                    match = re.match(pattern, line)
                    if match:
                        num, text, page_num = match.groups()
                        level = "H1" if '.' not in num else "H2"

                        headings.append({
                            "level": level,
                            "text": f"{num} {text}",
                            "page": int(page_num),
                            "position": i,
                            "confidence": 0.5
                        })
                        break

        return headings

    def _is_noise_line(self, line: str) -> bool:
        noise_patterns = [
            r'^copyright\s*[©]?',
            r'^version\s+\d+',
            r'^page\s+\d+',
            r'^\d{4}$',  # Just a year
            r'^[©]',
            r'^\d+$',  # Just a number
            r'^[ivx]+$',  # Roman numerals only
            r'^www\.',  # URLs
            r'^https?://',  # URLs
            r'^\s*$',  # Empty or whitespace only
        ]

        line_lower = line.lower()
        return any(re.match(pattern, line_lower) for pattern in noise_patterns)

    def _clean_heading_text(self, text: str) -> str:
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove trailing dots and page numbers
        text = re.sub(r'\.+\s*\d*\s*$', '', text)
        text = text.strip()
        return text

    def _is_valid_heading(self, text: str, line_index: int) -> bool:
        if not text or len(text) < 3 or len(text) > 200:
            return False

        if text.isdigit():
            return False

        # Check for too many special characters (likely not a heading)
        special_char_count = sum(1 for c in text if not c.isalnum() and c != ' ')
        if special_char_count > len(text) * 0.3:
            return False

        context_score = 0

        # Check previous line context
        if line_index > 0:
            prev_line = self.lines[line_index - 1].strip()
            if len(prev_line) < 20 or not prev_line:
                context_score += 1

        # Check next line context
        if line_index < len(self.lines) - 1:
            next_line = self.lines[line_index + 1].strip()
            if not next_line or (next_line and next_line[0].isupper()):
                context_score += 1

        return context_score >= 1

    def _clean_and_process_headings(self, headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Sort by confidence (descending) and position (ascending)
        headings.sort(key=lambda x: (-x['confidence'], x['position']))

        seen = set()
        unique_headings = []

        for heading in headings:
            # Create a key for deduplication
            key = (heading['text'].lower().strip(), heading['page'])
            if key not in seen:
                seen.add(key)
                clean_heading = {
                    "level": heading["level"],
                    "text": heading["text"],
                    "page": heading["page"]
                }
                unique_headings.append(clean_heading)

        # Sort final headings by position to maintain document order
        unique_headings.sort(key=lambda x: next(h['position'] for h in headings
                                              if h['text'] == x['text'] and h['page'] == x['page']))

        return unique_headings

    def _determine_document_title(self, headings: List[Dict[str, Any]]) -> str:
        if not headings:
            return "Unknown Document"

        # Look for title in first 10 lines
        for line in self.lines[:10]:
            if (len(line) > 10 and
                not re.match(r'^\d+\.', line) and
                not self._is_noise_line(line) and
                not line.lower().startswith('page ')):
                return line

        # If no title found, use first heading
        if headings:
            return headings[0]['text']

        return "Unknown Document"


def extract_headings_from_pdf_text(pdf_text: str) -> Dict[str, Any]:
    """Extract headings from PDF text using advanced pattern matching."""
    extractor = AdvancedPDFHeadingExtractor(pdf_text)
    return extractor.extract_headings()


def extract_text_with_ocr(pdf_path: str) -> str:
    """Extract text from PDF using OCR (requires pdf2image and pytesseract)."""
    try:
        from pdf2image import convert_from_path
        import pytesseract

        pages = convert_from_path(pdf_path)
        text = ""

        for page_num, page_image in enumerate(pages, 1):
            page_text = pytesseract.image_to_string(page_image)
            text += f"\nPage {page_num} of {len(pages)}\n"
            text += page_text + "\n"

        return text
    except ImportError as e:
        raise ImportError(f"Required libraries not installed: {e}")
    except Exception as e:
        raise Exception(f"Error during OCR processing: {e}")


def extract_text_with_pdfplumber(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber (requires pdfplumber)."""
    try:
        import pdfplumber

        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += f"\nPage {page_num} of {len(pdf.pages)}\n"
                    text += page_text + "\n"

        return text
    except ImportError as e:
        raise ImportError(f"pdfplumber not installed: {e}")
    except Exception as e:
        raise Exception(f"Error during PDF processing: {e}")


# Example usage
if __name__ == "__main__":
    try:
        # Choose your extraction method
        pdf_text = extract_text_with_ocr("data/123.pdf")
        # or: pdf_text = extract_text_with_pdfplumber("data/123.pdf")

        result = extract_headings_from_pdf_text(pdf_text)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
