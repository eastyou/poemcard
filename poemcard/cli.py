from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import NoReturn, Optional, Sequence

from .model import BUILTIN_POEMS, Poem, PoemError, read_poems
from .render import render_cards, render_guide_blanks


class _PoemArgumentParser(argparse.ArgumentParser):
    """把 argparse 的英文参数错误转换为中文异常。"""

    def error(self, message: str) -> NoReturn:
        raise PoemError(f"参数错误：{message}")


def _build_parser() -> argparse.ArgumentParser:
    parser = _PoemArgumentParser(
        prog="poemcard",
        description="把古诗排成竖排 A4 展示卡与书写稿纸。",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="poemcard.html",
        help="输出 HTML 路径（默认 poemcard.html）",
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="input_path",
        default=None,
        help="读取自定义诗稿文件（UTF-8 或 GBK）",
    )
    parser.add_argument(
        "--poem",
        default=None,
        help="按标题筛选内置古诗，例如 --poem 静夜思",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all_poems",
        help="生成全部内置古诗（默认行为）",
    )
    parser.add_argument(
        "--grid",
        action="store_true",
        help="在文字下叠加稿纸方格",
    )
    parser.add_argument(
        "--blank",
        action="store_true",
        help="生成描红临写页（淡色原诗 + 空白方格）",
    )
    parser.add_argument(
        "--title",
        default="古诗竖排卡",
        help="页面标题（默认「古诗竖排卡」）",
    )
    return parser


def _load_poems(args: argparse.Namespace) -> list[Poem]:
    """根据命令行参数选择内置诗或读取外部诗稿。"""
    if args.input_path is not None:
        if not isinstance(args.input_path, str) or not args.input_path.strip():
            raise PoemError("--input 不能为空")
        if args.poem is not None:
            raise PoemError("--poem 不能与 --input 同时使用")
        return read_poems(Path(args.input_path))

    if args.poem is not None:
        if args.all_poems:
            raise PoemError("--poem 不能与 --all 同时使用")
        keyword = args.poem.strip()
        if not keyword:
            raise PoemError("--poem 不能为空")
        matched = [poem for poem in BUILTIN_POEMS if poem.title == keyword]
        if not matched:
            raise PoemError(f"未找到标题为「{keyword}」的内置古诗")
        return matched

    return list(BUILTIN_POEMS)


def _write_output(path: Path, content: str) -> None:
    """把 HTML 写入目标路径，失败时抛出 OSError。"""
    if not isinstance(content, str) or not content:
        raise PoemError("生成的页面内容为空")
    path.write_text(content, encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """命令行入口：成功返回 0，输入非法返回 2，文件读写失败返回 1。"""
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        poems = _load_poems(args)

        doc_title = args.title.strip() if isinstance(args.title, str) else ""
        if not doc_title:
            raise PoemError("--title 不能为空")

        if args.blank:
            content = render_guide_blanks(poems, title=doc_title)
        else:
            content = render_cards(poems, grid=args.grid, title=doc_title)

        output = args.output
        if not isinstance(output, str) or not output.strip():
            raise PoemError("输出路径不能为空")
        _write_output(Path(output), content)
    except PoemError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"文件不存在：{exc}", file=sys.stderr)
        return 1
    except UnicodeEncodeError as exc:
        print(f"写入失败：{exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"文件读写失败：{exc}", file=sys.stderr)
        return 1

    print(f"已生成 {args.output}（{len(poems)} 首）")
    return 0
