from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from poemcard.cli import main
from poemcard.model import BUILTIN_POEMS


def run_cli(argv: list[str]) -> tuple[int, str, str]:
    """运行命令行入口并捕获退出码、标准输出与标准错误。"""
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def _output(self) -> Path:
        return self.dir / "cards.html"

    def test_default_generates_all_builtin_poems(self) -> None:
        output = self._output()
        code, stdout, stderr = run_cli(["-o", str(output)])
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertTrue(output.exists())
        content = output.read_text(encoding="utf-8")
        self.assertEqual(
            len(BUILTIN_POEMS), content.count('<section class="page">')
        )
        self.assertIn(f"（{len(BUILTIN_POEMS)} 首）", stdout)
        self.assertTrue(stdout.startswith("已生成 "))

    def test_default_output_filename(self) -> None:
        old_cwd = os.getcwd()
        os.chdir(self.dir)
        try:
            code, _stdout, _stderr = run_cli([])
        finally:
            os.chdir(old_cwd)
        self.assertEqual(0, code)
        self.assertTrue((self.dir / "poemcard.html").exists())

    def test_poem_filter(self) -> None:
        output = self._output()
        code, stdout, _stderr = run_cli(["-o", str(output), "--poem", "静夜思"])
        self.assertEqual(0, code)
        content = output.read_text(encoding="utf-8")
        self.assertEqual(1, content.count('<section class="page">'))
        self.assertIn("静夜思", content)
        self.assertIn("（1 首）", stdout)

    def test_unknown_poem_returns_two(self) -> None:
        output = self._output()
        code, _stdout, stderr = run_cli(["-o", str(output), "--poem", "不存在的诗"])
        self.assertEqual(2, code)
        self.assertIn("未找到", stderr)
        self.assertFalse(output.exists())

    def test_all_flag(self) -> None:
        output = self._output()
        code, stdout, _stderr = run_cli(["-o", str(output), "--all"])
        self.assertEqual(0, code)
        self.assertIn(f"（{len(BUILTIN_POEMS)} 首）", stdout)

    def test_poem_and_all_conflict(self) -> None:
        code, _stdout, stderr = run_cli(["--poem", "静夜思", "--all"])
        self.assertEqual(2, code)
        self.assertIn("同时使用", stderr)

    def test_input_file(self) -> None:
        source = self.dir / "poems.txt"
        source.write_text(
            "春江|佚名\n春江潮水连海平，\n海上明月共潮生。\n", encoding="utf-8"
        )
        output = self._output()
        code, _stdout, _stderr = run_cli(["-i", str(source), "-o", str(output)])
        self.assertEqual(0, code)
        content = output.read_text(encoding="utf-8")
        self.assertIn("春江", content)
        for char in "春江潮水连海平，":
            self.assertIn(char, content)

    def test_input_file_gbk(self) -> None:
        source = self.dir / "poems-gbk.txt"
        source.write_bytes("春晓|孟浩然\n春眠不觉晓，\n".encode("gbk"))
        output = self._output()
        code, _stdout, _stderr = run_cli(["-i", str(source), "-o", str(output)])
        self.assertEqual(0, code)
        content = output.read_text(encoding="utf-8")
        self.assertIn("春晓", content)
        for char in "春眠不觉晓，":
            self.assertIn(char, content)

    def test_missing_input_returns_one(self) -> None:
        code, _stdout, stderr = run_cli(
            ["-i", str(self.dir / "missing.txt"), "-o", str(self._output())]
        )
        self.assertEqual(1, code)
        self.assertIn("找不到输入文件", stderr)

    def test_invalid_input_returns_two(self) -> None:
        source = self.dir / "bad.txt"
        source.write_text("没有分隔符\n床前明月光，\n", encoding="utf-8")
        code, _stdout, stderr = run_cli(["-i", str(source), "-o", str(self._output())])
        self.assertEqual(2, code)
        self.assertIn("格式错误", stderr)

    def test_undecodable_input_returns_two(self) -> None:
        source = self.dir / "binary.txt"
        source.write_bytes(b"\xff\xff\xff")
        code, _stdout, stderr = run_cli(["-i", str(source), "-o", str(self._output())])
        self.assertEqual(2, code)
        self.assertIn("无法解码", stderr)

    def test_input_and_poem_conflict(self) -> None:
        source = self.dir / "poems.txt"
        source.write_text("春江|佚名\n春江潮水连海平，\n", encoding="utf-8")
        code, _stdout, stderr = run_cli(
            ["-i", str(source), "--poem", "静夜思", "-o", str(self._output())]
        )
        self.assertEqual(2, code)
        self.assertIn("同时使用", stderr)

    def test_empty_input_path_returns_two(self) -> None:
        code, _stdout, stderr = run_cli(["-i", "   ", "-o", str(self._output())])
        self.assertEqual(2, code)
        self.assertIn("--input 不能为空", stderr)

    def test_grid_flag(self) -> None:
        output = self._output()
        code, _stdout, _stderr = run_cli(["-o", str(output), "--poem", "静夜思", "--grid"])
        self.assertEqual(0, code)
        self.assertIn('<rect class="cell"', output.read_text(encoding="utf-8"))

    def test_blank_flag(self) -> None:
        output = self._output()
        code, _stdout, _stderr = run_cli(["-o", str(output), "--poem", "静夜思", "--blank"])
        self.assertEqual(0, code)
        content = output.read_text(encoding="utf-8")
        self.assertIn("先描红", content)
        self.assertIn('fill="#d4d0c6"', content)

    def test_custom_title(self) -> None:
        output = self._output()
        code, _stdout, _stderr = run_cli(["-o", str(output), "--title", "三年级展示"])
        self.assertEqual(0, code)
        self.assertIn("<title>三年级展示</title>", output.read_text(encoding="utf-8"))

    def test_blank_title_returns_two(self) -> None:
        code, _stdout, stderr = run_cli(["-o", str(self._output()), "--title", "   "])
        self.assertEqual(2, code)
        self.assertIn("--title 不能为空", stderr)

    def test_empty_output_path_returns_two(self) -> None:
        code, _stdout, stderr = run_cli(["-o", "  "])
        self.assertEqual(2, code)
        self.assertIn("输出路径不能为空", stderr)

    def test_unknown_option_returns_two(self) -> None:
        code, _stdout, stderr = run_cli(["--unknown-option"])
        self.assertEqual(2, code)
        self.assertIn("参数错误", stderr)

    def test_blank_poem_argument_returns_two(self) -> None:
        code, _stdout, stderr = run_cli(["--poem", "   "])
        self.assertEqual(2, code)
        self.assertIn("--poem 不能为空", stderr)

    def test_missing_output_directory_returns_one(self) -> None:
        output = self.dir / "not-exist" / "cards.html"
        code, _stdout, stderr = run_cli(["-o", str(output), "--poem", "静夜思"])
        self.assertEqual(1, code)
        self.assertIn("文件不存在", stderr)


if __name__ == "__main__":
    unittest.main()
