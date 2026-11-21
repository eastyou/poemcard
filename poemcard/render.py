from __future__ import annotations

import html
from typing import Sequence

from .model import Poem, PoemError, layout_columns, validate_poem

# SVG 场景坐标：与 A4 保持近似比例，实际尺寸由 CSS 控制。
_SCENE_WIDTH = 720.0
_SCENE_HEIGHT = 1000.0
_BODY_TOP = 170.0
_BODY_BOTTOM = 942.0
_BODY_LEFT = 56.0
_BODY_RIGHT = 664.0

_FONT_STACK = '"Kaiti SC","STKaiti","KaiTi",serif'


def _cell_rect(x_center: float, y_center: float, pitch: float) -> str:
    """生成一个稿纸方格。"""
    size = pitch * 0.92
    return (
        f'<rect class="cell" x="{x_center - size / 2:.2f}" '
        f'y="{y_center - size / 2:.2f}" width="{size:.2f}" '
        f'height="{size:.2f}" fill="none" stroke="#c8c2b4" stroke-width="1"/>'
    )


def _char_text(
    char: str,
    col: int,
    row: int,
    x_center: float,
    y_center: float,
    font_size: float,
    fill: str,
) -> str:
    """生成逐字定位的竖排文字元素。"""
    baseline = y_center + font_size * 0.34
    return (
        f'<text class="poem-char" data-col="{col}" data-row="{row}" '
        f'x="{x_center:.2f}" y="{baseline:.2f}" font-size="{font_size:.2f}" '
        f'text-anchor="middle" fill="{fill}">{html.escape(char)}</text>'
    )


def _header_svg(poem: Poem, blank: bool) -> str:
    """生成标题与作者区域（横排居中）。"""
    title = poem.title.strip()
    title_size = max(26.0, min(48.0, 560.0 / max(len(title), 1)))
    parts = [
        f'<text class="poem-title" x="{_SCENE_WIDTH / 2:.1f}" y="72" '
        f'font-size="{title_size:.1f}" text-anchor="middle" fill="#161616">'
        f"{html.escape(title)}</text>",
        f'<text class="poem-author" x="{_SCENE_WIDTH / 2:.1f}" y="116" '
        f'font-size="22" text-anchor="middle" fill="#5a5a5a">'
        f"{html.escape(poem.author.strip())}</text>",
    ]
    if blank:
        parts.append(
            f'<text class="poem-hint" x="{_SCENE_WIDTH / 2:.1f}" y="152" '
            f'font-size="18" text-anchor="middle" fill="#8a8578">'
            "先描红，再在空格中临写</text>"
        )
    return "".join(parts)


def _page_svg(poem: Poem, grid: bool, blank: bool) -> str:
    """把一首诗渲染为一页 SVG（逐字定位，自右向左分列）。"""
    columns = layout_columns(poem)
    max_rows = max(len(column) for column in columns)
    column_total = len(columns) + (1 if blank else 0)
    pitch = min(
        (_BODY_BOTTOM - _BODY_TOP) / max_rows,
        (_BODY_RIGHT - _BODY_LEFT) / column_total,
    )
    font_size = pitch * 0.8
    fill = "#d4d0c6" if blank else "#191919"

    parts = [
        f'<rect class="sheet" x="0" y="0" width="{_SCENE_WIDTH:.0f}" '
        f'height="{_SCENE_HEIGHT:.0f}" fill="#fffdf8"/>',
        _header_svg(poem, blank),
        '<g class="poem-body">',
    ]

    for col_index, column in enumerate(columns):
        x_center = _BODY_RIGHT - (col_index + 0.5) * pitch
        for row_index, char in enumerate(column):
            y_center = _BODY_TOP + (row_index + 0.5) * pitch
            if grid or blank:
                parts.append(_cell_rect(x_center, y_center, pitch))
            parts.append(
                _char_text(
                    char, col_index, row_index, x_center, y_center, font_size, fill
                )
            )

    if blank:
        # 最左侧留一列空白格，供学生独立临写。
        x_center = _BODY_RIGHT - (len(columns) + 0.5) * pitch
        for row_index in range(max_rows):
            y_center = _BODY_TOP + (row_index + 0.5) * pitch
            parts.append(_cell_rect(x_center, y_center, pitch))

    parts.append("</g>")
    aria = f"{poem.title.strip()} 竖排临写页" if blank else f"{poem.title.strip()} 竖排卡片"
    return (
        f'<svg class="poem-svg" viewBox="0 0 {_SCENE_WIDTH:.0f} {_SCENE_HEIGHT:.0f}" '
        f'role="img" aria-label="{html.escape(aria, quote=True)}">'
        + "".join(parts)
        + "</svg>"
    )


def _document(pages: Sequence[str], title: str) -> str:
    """把若干页 SVG 包装成完整的 A4 HTML 文档。"""
    if not isinstance(title, str) or not title.strip():
        raise PoemError("页面标题不能为空")
    if not pages:
        raise PoemError("至少需要一页内容")

    safe_title = html.escape(title.strip())
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{safe_title}</title>
<style>
@page {{ size: A4; margin: 0; }}
html, body {{ margin: 0; padding: 0; }}
body {{
  background: #e9e6df;
  color: #1b1b1b;
  font-family: {_FONT_STACK};
}}
.page {{
  width: 210mm;
  min-height: 297mm;
  padding: 12mm;
  box-sizing: border-box;
  overflow: hidden;
  background: #fffdf8;
  display: flex;
  align-items: center;
  justify-content: center;
  page-break-after: always;
}}
.page:last-child {{ page-break-after: auto; }}
.poem-svg {{ width: 100%; height: auto; display: block; }}
.poem-svg text {{ font-family: {_FONT_STACK}; }}
@media screen {{
  .page {{ margin: 8mm auto; box-shadow: 0 2mm 6mm rgba(0, 0, 0, 0.12); }}
}}
@media print {{
  body {{ background: #fff; }}
  .page {{ margin: 0; box-shadow: none; }}
}}
</style>
</head>
<body>
{"".join(f'<section class="page">{page}</section>' for page in pages)}
</body>
</html>
"""


def render_cards(
    poems: Sequence[Poem], grid: bool = False, title: str = "古诗竖排卡"
) -> str:
    """渲染 A4 展示卡，每首诗一页。

    ``grid`` 为真时叠加稿纸方格；所有文字都经过 HTML 转义。
    """
    if poems is None:
        raise PoemError("古诗列表不能为空")
    poem_list = list(poems)
    if not poem_list:
        raise PoemError("至少需要一首古诗")

    pages = []
    for poem in poem_list:
        validate_poem(poem)
        pages.append(_page_svg(poem, grid=grid, blank=False))
    return _document(pages, title)


def render_guide_blanks(
    poems: Sequence[Poem], title: str = "古诗临写页"
) -> str:
    """渲染多首诗的描红临写页，每首诗一页。"""
    if poems is None:
        raise PoemError("古诗列表不能为空")
    poem_list = list(poems)
    if not poem_list:
        raise PoemError("至少需要一首古诗")

    pages = []
    for poem in poem_list:
        validate_poem(poem)
        pages.append(_page_svg(poem, grid=True, blank=True))
    return _document(pages, title)


def render_guide_blank(poem: Poem, title: str = "古诗临写页") -> str:
    """渲染单首诗的描红临写页：淡色原诗 + 空白方格。"""
    return render_guide_blanks((poem,), title=title)
