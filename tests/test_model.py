from __future__ import annotations

import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from poemcard.model import (
    BUILTIN_POEMS,
    MAX_LINE_CHARS,
    MAX_POEM_LINES,
    Poem,
    PoemError,
    grid_size_for,
    layout_columns,
    parse_poem_text,
    read_poems,
    validate_poem,
)


class BuiltinPoemsTest(unittest.TestCase):
    def test_builtin_count_at_least_ten(self) -> None:
        self.assertGreaterEqual(len(BUILTIN_POEMS), 10)

    def test_builtin_titles_are_unique(self) -> None:
        titles = [poem.title for poem in BUILTIN_POEMS]
        self.assertEqual(len(titles), len(set(titles)))

    def test_builtin_contains_required_titles(self) -> None:
        required = {
            "静夜思",
            "春晓",
            "登鹳雀楼",
            "悯农",
            "江雪",
            "咏鹅",
            "望庐山瀑布",
            "绝句",
            "山行",
            "小池",
        }
        self.assertTrue(required.issubset({poem.title for poem in BUILTIN_POEMS}))

    def test_builtin_poems_are_valid(self) -> None:
        for poem in BUILTIN_POEMS:
            self.assertIsNone(validate_poem(poem))

    def test_builtin_poems_have_four_lines(self) -> None:
        for poem in BUILTIN_POEMS:
            self.assertEqual(4, len(poem.lines), poem.title)

    def test_builtin_lines_within_limits(self) -> None:
        for poem in BUILTIN_POEMS:
            for line in poem.lines:
                self.assertTrue(line.strip())
                self.assertLessEqual(len(line), MAX_LINE_CHARS)


class ParsePoemTextTest(unittest.TestCase):
    SAMPLE = (
        "静夜思|李白\n"
        "床前明月光，\n"
        "疑是地上霜。\n"
        "\n"
        "春晓|孟浩然\n"
        "春眠不觉晓，\n"
        "处处闻啼鸟。\n"
    )

    def test_parse_single_poem(self) -> None:
        poems = parse_poem_text("静夜思|李白\n床前明月光，\n疑是地上霜。\n")
        self.assertEqual(1, len(poems))
        self.assertEqual("静夜思", poems[0].title)
        self.assertEqual("李白", poems[0].author)
        self.assertEqual(("床前明月光，", "疑是地上霜。"), poems[0].lines)

    def test_parse_multiple_poems(self) -> None:
        poems = parse_poem_text(self.SAMPLE)
        self.assertEqual(["静夜思", "春晓"], [poem.title for poem in poems])

    def test_parse_strips_whitespace(self) -> None:
        poems = parse_poem_text(" 静夜思 | 李白 \n  床前明月光，  \n 疑是地上霜。 \n")
        self.assertEqual("静夜思", poems[0].title)
        self.assertEqual("李白", poems[0].author)
        self.assertEqual("床前明月光，", poems[0].lines[0])

    def test_parse_empty_text_raises(self) -> None:
        with self.assertRaises(PoemError):
            parse_poem_text("")

    def test_parse_blank_text_raises(self) -> None:
        with self.assertRaises(PoemError):
            parse_poem_text("  \n\t\n")

    def test_parse_non_string_raises(self) -> None:
        with self.assertRaises(PoemError):
            parse_poem_text(None)  # type: ignore[arg-type]

    def test_parse_missing_separator_raises(self) -> None:
        with self.assertRaises(PoemError):
            parse_poem_text("静夜思\n床前明月光，\n")

    def test_parse_multiple_separators_raises(self) -> None:
        with self.assertRaises(PoemError):
            parse_poem_text("静夜思|李白|唐\n床前明月光，\n")

    def test_parse_empty_title_raises(self) -> None:
        with self.assertRaises(PoemError):
            parse_poem_text("|李白\n床前明月光，\n")

    def test_parse_empty_author_raises(self) -> None:
        with self.assertRaises(PoemError):
            parse_poem_text("静夜思|\n床前明月光，\n")

    def test_parse_without_lines_raises(self) -> None:
        with self.assertRaises(PoemError):
            parse_poem_text("静夜思|李白\n\n春晓|孟浩然\n春眠不觉晓，\n")

    def test_parse_too_many_lines_raises(self) -> None:
        body = "\n".join(["床前明月光，"] * (MAX_POEM_LINES + 1))
        with self.assertRaises(PoemError):
            parse_poem_text(f"静夜思|李白\n{body}\n")

    def test_parse_line_too_long_raises(self) -> None:
        with self.assertRaises(PoemError):
            parse_poem_text("静夜思|李白\n" + "一" * (MAX_LINE_CHARS + 1) + "\n")

    def test_parse_pipe_in_line_raises(self) -> None:
        with self.assertRaises(PoemError):
            parse_poem_text("静夜思|李白\n床前|明月光，\n")

    def test_parse_allows_max_length_line(self) -> None:
        poems = parse_poem_text("静夜思|李白\n" + "一" * MAX_LINE_CHARS + "\n")
        self.assertEqual(MAX_LINE_CHARS, len(poems[0].lines[0]))


class ReadPoemsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def test_read_utf8(self) -> None:
        path = self.dir / "poems.txt"
        path.write_text("静夜思|李白\n床前明月光，\n", encoding="utf-8")
        poems = read_poems(path)
        self.assertEqual("静夜思", poems[0].title)

    def test_read_utf8_bom(self) -> None:
        path = self.dir / "poems-bom.txt"
        content = "静夜思|李白\n床前明月光，\n"
        path.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))
        poems = read_poems(path)
        self.assertEqual("静夜思", poems[0].title)

    def test_read_gbk_fallback(self) -> None:
        path = self.dir / "poems-gbk.txt"
        path.write_bytes("春晓|孟浩然\n春眠不觉晓，\n".encode("gbk"))
        poems = read_poems(path)
        self.assertEqual("春晓", poems[0].title)

    def test_read_missing_file_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            read_poems(self.dir / "missing.txt")

    def test_read_undecodable_file_raises(self) -> None:
        path = self.dir / "binary.txt"
        path.write_bytes(b"\xff\xff\xff")
        with self.assertRaises(PoemError):
            read_poems(path)

    def test_read_invalid_format_raises(self) -> None:
        path = self.dir / "bad.txt"
        path.write_text("没有分隔符\n床前明月光，\n", encoding="utf-8")
        with self.assertRaises(PoemError):
            read_poems(path)


class LayoutColumnsTest(unittest.TestCase):
    def test_columns_follow_line_order(self) -> None:
        poem = Poem("测试", "佚名", ("甲乙丙", "丁戊"))
        self.assertEqual([["甲", "乙", "丙"], ["丁", "戊"]], layout_columns(poem))

    def test_first_column_is_first_line(self) -> None:
        poem = BUILTIN_POEMS[0]
        columns = layout_columns(poem)
        self.assertEqual(list(poem.lines[0].strip()), columns[0])

    def test_punctuation_occupies_its_own_cell(self) -> None:
        poem = Poem("测试", "佚名", ("床前明月光，",))
        columns = layout_columns(poem)
        self.assertEqual(6, len(columns[0]))
        self.assertEqual("，", columns[0][-1])

    def test_layout_invalid_poem_raises(self) -> None:
        with self.assertRaises(PoemError):
            layout_columns(Poem("", "佚名", ("甲",)))

    def test_layout_columns_count(self) -> None:
        self.assertEqual(4, len(layout_columns(BUILTIN_POEMS[1])))


class GridSizeTest(unittest.TestCase):
    def test_grid_size_basic(self) -> None:
        self.assertEqual((4, 6), grid_size_for(BUILTIN_POEMS[0]))

    def test_grid_size_zero_means_unlimited(self) -> None:
        self.assertEqual((4, 6), grid_size_for(BUILTIN_POEMS[0], 0))

    def test_grid_size_respects_columns_per_page(self) -> None:
        self.assertEqual((2, 12), grid_size_for(BUILTIN_POEMS[0], 2))

    def test_grid_size_larger_limit_keeps_one_band(self) -> None:
        self.assertEqual((4, 6), grid_size_for(BUILTIN_POEMS[0], 10))

    def test_grid_size_negative_raises(self) -> None:
        with self.assertRaises(PoemError):
            grid_size_for(BUILTIN_POEMS[0], -1)

    def test_grid_size_non_int_raises(self) -> None:
        with self.assertRaises(PoemError):
            grid_size_for(BUILTIN_POEMS[0], "2")  # type: ignore[arg-type]


class ValidatePoemTest(unittest.TestCase):
    def test_valid_poem_passes(self) -> None:
        self.assertIsNone(validate_poem(BUILTIN_POEMS[0]))

    def test_non_poem_raises(self) -> None:
        with self.assertRaises(PoemError):
            validate_poem("静夜思")  # type: ignore[arg-type]

    def test_empty_title_raises(self) -> None:
        with self.assertRaises(PoemError):
            validate_poem(Poem("  ", "李白", ("甲",)))

    def test_empty_author_raises(self) -> None:
        with self.assertRaises(PoemError):
            validate_poem(Poem("静夜思", "", ("甲",)))

    def test_empty_lines_raises(self) -> None:
        with self.assertRaises(PoemError):
            validate_poem(Poem("静夜思", "李白", ()))

    def test_too_many_lines_raises(self) -> None:
        with self.assertRaises(PoemError):
            validate_poem(Poem("长诗", "佚名", ("甲",) * (MAX_POEM_LINES + 1)))

    def test_blank_line_raises(self) -> None:
        with self.assertRaises(PoemError):
            validate_poem(Poem("静夜思", "李白", ("甲", "  ")))

    def test_line_too_long_raises(self) -> None:
        with self.assertRaises(PoemError):
            validate_poem(Poem("长句", "佚名", ("一" * (MAX_LINE_CHARS + 1),)))

    def test_non_string_line_raises(self) -> None:
        with self.assertRaises(PoemError):
            validate_poem(Poem("静夜思", "李白", (123,)))  # type: ignore[arg-type]

    def test_poem_is_frozen(self) -> None:
        poem = Poem("静夜思", "李白", ("甲",))
        with self.assertRaises(FrozenInstanceError):
            poem.title = "春晓"  # type: ignore[misc]

    def test_poem_error_is_value_error(self) -> None:
        self.assertTrue(issubclass(PoemError, ValueError))


if __name__ == "__main__":
    unittest.main()
