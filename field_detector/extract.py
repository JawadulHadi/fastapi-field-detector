"""Stage 1: pull words, horizontal lines and checkbox squares out of a PDF page."""
from dataclasses import dataclass

import pymupdf


@dataclass
class Word:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class HLine:
    x0: float
    x1: float
    y: float


@dataclass
class Square:
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass
class PageData:
    number: int  # 1-based
    width: float
    height: float
    segments: list[list[Word]]  # words grouped into label-sized clusters
    lines: list[HLine]
    squares: list[Square]


GAP = 30  # points of whitespace that start a new segment on the same text line


def _segments(words: list[tuple]) -> list[list[Word]]:
    by_line: dict[tuple, list[Word]] = {}
    for x0, y0, x1, y1, text, block, line, _ in words:
        by_line.setdefault((block, line), []).append(Word(text, x0, y0, x1, y1))
    out: list[list[Word]] = []
    for ws in by_line.values():
        ws.sort(key=lambda w: w.x0)
        current = [ws[0]]
        for w in ws[1:]:
            if w.x0 - current[-1].x1 > GAP:
                out.append(current)
                current = []
            current.append(w)
        out.append(current)
    return out


def extract_page(page: pymupdf.Page, number: int) -> PageData:
    lines: list[HLine] = []
    squares: list[Square] = []
    for drawing in page.get_drawings():
        for item in drawing['items']:
            if item[0] == 'l':
                p1, p2 = item[1], item[2]
                if abs(p1.y - p2.y) < 1 and abs(p1.x - p2.x) > 30:
                    lines.append(HLine(min(p1.x, p2.x), max(p1.x, p2.x), p1.y))
            elif item[0] == 're':
                r = item[1]
                if r.height < 2 and r.width > 30:
                    lines.append(HLine(r.x0, r.x1, r.y0))
                elif 6 <= r.width <= 18 and abs(r.width - r.height) < 2:
                    squares.append(Square(r.x0, r.y0, r.x1, r.y1))
    return PageData(number, page.rect.width, page.rect.height,
                    _segments(page.get_text('words')), lines, squares)
