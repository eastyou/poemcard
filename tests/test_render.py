from __future__ import annotations

import html
import re
import unittest

from poemcard.model import BUILTIN_POEMS, Poem, PoemError
from poemcard.render import render_cards, render_guide_blank, render_guide_blanks

CHAR_PATTERN = re.compile(
    r'<text class="poem-char" data-col="(\d+)" data-row="(\d+)" '
    r'x="([0-9.]+)" y="([0-9.]+)" font-size="([0-9.]+)" text-anchor="middle" '
    r'fill="#[0-9a-fA-F]{6}">([^<]*)</text>'
)


def total_chars(poem: Poem) -> int:
    return sum(len(line.strip()) for line in poem.lines)


class RenderCardsTest(unittest.TestCase):
    def test_document_structure(self) -> None:
        result = render_cards([BUILTIN_POEMS[0]])
        self.assertTrue(result.startswith("<!DOCTYPE html>"))
        self.assertIn('<meta charset="utf-8">', result)
        self.assertIn("</html>", result)

    def test_each_poem_gets_one_page(self) -> None:
        result = render_cards(BUILTIN_POEMS[:3])
        self.assertEqual(3, result.count('<section class="page">'))

    def test_all_poem_characters_are_rendered(self) -> None:
        for poem in BUILTIN_POEMS[:4]:
            result = render_cards([poem])
            for line in poem.lines:
                for char in line:
                    self.assertIn(html.escape(char), result, poem.title)

    def test_title_and_author_are_rendered(self) -> None:
        result = render_cards([BUILTIN_POEMS[0]])
        self.assertIn("静夜思", result)
        self.assertIn("李白", result)

    def test_character_count_matches_poem(self) -> None:
        poem = BUILTIN_POEMS[0]
        result = render_cards([poem])
        self.assertEqual(total_chars(poem), len(CHAR_PATTERN.findall(result)))

    def test_column_x_decreases_right_to_left(self) -> None:
        result = render_cards([BUILTIN_POEMS[0]])
        positions: dict[int, list[tuple[int, float]]] = {}
        for col, row, x, _y, _size, _char in CHAR_PATTERN.findall(result):
            positions.setdefault(int(col), []).append((int(row), float(x)))

        self.assertEqual([0, 1, 2, 3], sorted(positions))
        column_x = [positions[col][0][1] for col in sorted(positions)]
        self.assertEqual(column_x, sorted(column_x, reverse=True))
        self.assertGreater(column_x[0], column_x[-1])

    def test_row_y_increases_top_to_bottom(self) -> None:
        result = render_cards([BUILTIN_POEMS[0]])
        first_column = sorted(
            (int(row), float(y))
            for col, row, _x, y, _size, _char in CHAR_PATTERN.findall(result)
            if int(col) == 0
        )
        ys = [y for _row, y in first_column]
        self.assertEqual(ys, sorted(ys))

    def test_character_order_within_column(self) -> None:
        poem = BUILTIN_POEMS[0]
        result = render_cards([poem])
        chars = [
            char
            for col, _row, _x, _y, _size, char in CHAR_PATTERN.findall(result)
            if int(col) == 0
        ]
        self.assertEqual([html.escape(c) for c in poem.lines[0]], chars)

    def test_grid_cells_match_character_count(self) -> None:
        poem = BUILTIN_POEMS[0]
        result = render_cards([poem], grid=True)
        self.assertEqual(total_chars(poem), result.count('<rect class="cell"'))

    def test_no_grid_cells_without_grid_flag(self) -> None:
        result = render_cards([BUILTIN_POEMS[0]])
        self.assertNotIn('<rect class="cell"', result)

    def test_html_is_escaped(self) -> None:
        poem = Poem('<唐诗&>', '李"白"', ("<甲>", "乙&丙"))
        result = render_cards([poem])
        self.assertIn("&lt;唐诗&amp;&gt;", result)
        self.assertIn("李&quot;白&quot;", result)
        self.assertNotIn("<唐诗", result)
        first_column = [
            char
            for col, _row, _x, _y, _size, char in CHAR_PATTERN.findall(result)
            if int(col) == 0
        ]
        self.assertEqual(["&lt;", "甲", "&gt;"], first_column)
        self.assertIn("&amp;", result)
        self.assertNotIn("<甲>", result)

    def test_document_title_is_escaped(self) -> None:
        result = render_cards([BUILTIN_POEMS[0]], title="<我的卡>")
        self.assertIn("<title>&lt;我的卡&gt;</title>", result)

    def test_a4_page_css(self) -> None:
        result = render_cards([BUILTIN_POEMS[0]])
        self.assertIn("@page { size: A4; margin: 0; }", result)
        self.assertIn("width: 210mm", result)
        self.assertIn("min-height: 297mm", result)
        self.assertIn("padding: 12mm", result)
        self.assertIn("overflow: hidden", result)

    def test_does_not_use_writing_mode(self) -> None:
        result = render_cards([BUILTIN_POEMS[0]])
        self.assertNotIn("writing-mode", result)

    def test_font_fallback_stack(self) -> None:
        result = render_cards([BUILTIN_POEMS[0]])
        self.assertIn('"Kaiti SC","STKaiti","KaiTi",serif', result)

    def test_coordinates_inside_scene(self) -> None:
        result = render_cards([BUILTIN_POEMS[0]])
        for _col, _row, x, y, _size, _char in CHAR_PATTERN.findall(result):
            self.assertGreater(float(x), 0.0)
            self.assertLess(float(x), 720.0)
            self.assertGreater(float(y), 0.0)
            self.assertLess(float(y), 1000.0)

    def test_empty_poems_raises(self) -> None:
        with self.assertRaises(PoemError):
            render_cards([])

    def test_invalid_poem_raises(self) -> None:
        with self.assertRaises(PoemError):
            render_cards([Poem("", "李白", ("甲",))])

    def test_empty_title_raises(self) -> None:
        with self.assertRaises(PoemError):
            render_cards([BUILTIN_POEMS[0]], title="  ")


class RenderGuideBlankTest(unittest.TestCase):
    def test_contains_pale_poem_and_hint(self) -> None:
        poem = BUILTIN_POEMS[0]
        result = render_guide_blank(poem)
        self.assertIn("先描红，再在空格中临写", result)
        self.assertEqual(total_chars(poem), result.count('fill="#d4d0c6"'))

    def test_blank_page_has_extra_empty_column(self) -> None:
        poem = BUILTIN_POEMS[0]
        result = render_guide_blank(poem)
        max_rows = max(len(line) for line in poem.lines)
        self.assertEqual(total_chars(poem) + max_rows, result.count('<rect class="cell"'))

    def test_blank_page_keeps_title_and_author(self) -> None:
        result = render_guide_blank(BUILTIN_POEMS[0])
        self.assertIn("静夜思", result)
        self.assertIn("李白", result)

    def test_blank_document_title(self) -> None:
        result = render_guide_blank(BUILTIN_POEMS[0])
        self.assertIn("<title>古诗临写页</title>", result)

    def test_blank_custom_title(self) -> None:
        result = render_guide_blank(BUILTIN_POEMS[0], title="三年级临写")
        self.assertIn("<title>三年级临写</title>", result)

    def test_guide_blanks_multiple_pages(self) -> None:
        result = render_guide_blanks(BUILTIN_POEMS[:2])
        self.assertEqual(2, result.count('<section class="page">'))

    def test_guide_blanks_empty_raises(self) -> None:
        with self.assertRaises(PoemError):
            render_guide_blanks([])

    def test_guide_blank_invalid_poem_raises(self) -> None:
        with self.assertRaises(PoemError):
            render_guide_blank(Poem("静夜思", "", ("甲",)))


if __name__ == "__main__":
    unittest.main()
