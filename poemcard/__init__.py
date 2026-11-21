"""poemcard：把古诗排成竖排 A4 展示卡与书写稿纸。"""

from __future__ import annotations

__version__ = "0.1.0"

from .model import BUILTIN_POEMS, Poem, PoemError, grid_size_for, layout_columns
from .render import render_cards, render_guide_blank, render_guide_blanks

__all__ = [
    "BUILTIN_POEMS",
    "Poem",
    "PoemError",
    "__version__",
    "grid_size_for",
    "layout_columns",
    "render_cards",
    "render_guide_blank",
    "render_guide_blanks",
]
