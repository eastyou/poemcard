from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# 单首诗最多允许的行数与单行最多允许的字数（含标点）。
MAX_POEM_LINES = 8
MAX_LINE_CHARS = 20


class PoemError(ValueError):
    """诗稿数据或命令行输入不合法时抛出的异常。"""


@dataclass(frozen=True)
class Poem:
    """一首古诗：标题、作者与逐行诗句（不含换行符）。"""

    title: str
    author: str
    lines: tuple[str, ...]


# 内置公版古诗，全部为四句，可直接用于课堂展示。
BUILTIN_POEMS: tuple[Poem, ...] = (
    Poem(
        title="静夜思",
        author="李白",
        lines=(
            "床前明月光，",
            "疑是地上霜。",
            "举头望明月，",
            "低头思故乡。",
        ),
    ),
    Poem(
        title="春晓",
        author="孟浩然",
        lines=(
            "春眠不觉晓，",
            "处处闻啼鸟。",
            "夜来风雨声，",
            "花落知多少。",
        ),
    ),
    Poem(
        title="登鹳雀楼",
        author="王之涣",
        lines=(
            "白日依山尽，",
            "黄河入海流。",
            "欲穷千里目，",
            "更上一层楼。",
        ),
    ),
    Poem(
        title="悯农",
        author="李绅",
        lines=(
            "锄禾日当午，",
            "汗滴禾下土。",
            "谁知盘中餐，",
            "粒粒皆辛苦。",
        ),
    ),
    Poem(
        title="江雪",
        author="柳宗元",
        lines=(
            "千山鸟飞绝，",
            "万径人踪灭。",
            "孤舟蓑笠翁，",
            "独钓寒江雪。",
        ),
    ),
    Poem(
        title="咏鹅",
        author="骆宾王",
        lines=(
            "鹅，鹅，鹅，",
            "曲项向天歌。",
            "白毛浮绿水，",
            "红掌拨清波。",
        ),
    ),
    Poem(
        title="望庐山瀑布",
        author="李白",
        lines=(
            "日照香炉生紫烟，",
            "遥看瀑布挂前川。",
            "飞流直下三千尺，",
            "疑是银河落九天。",
        ),
    ),
    Poem(
        title="绝句",
        author="杜甫",
        lines=(
            "两个黄鹂鸣翠柳，",
            "一行白鹭上青天。",
            "窗含西岭千秋雪，",
            "门泊东吴万里船。",
        ),
    ),
    Poem(
        title="山行",
        author="杜牧",
        lines=(
            "远上寒山石径斜，",
            "白云生处有人家。",
            "停车坐爱枫林晚，",
            "霜叶红于二月花。",
        ),
    ),
    Poem(
        title="小池",
        author="杨万里",
        lines=(
            "泉眼无声惜细流，",
            "树阴照水爱晴柔。",
            "小荷才露尖尖角，",
            "早有蜻蜓立上头。",
        ),
    ),
    Poem(
        title="鹿柴",
        author="王维",
        lines=(
            "空山不见人，",
            "但闻人语响。",
            "返景入深林，",
            "复照青苔上。",
        ),
    ),
    Poem(
        title="咏柳",
        author="贺知章",
        lines=(
            "碧玉妆成一树高，",
            "万条垂下绿丝绦。",
            "不知细叶谁裁出，",
            "二月春风似剪刀。",
        ),
    ),
)


def validate_poem(poem: Poem) -> None:
    """校验单首诗的数据是否合法，非法时抛出 :class:`PoemError`。"""
    if not isinstance(poem, Poem):
        raise PoemError("仅支持 Poem 对象")
    if not isinstance(poem.title, str) or not poem.title.strip():
        raise PoemError("标题不能为空")
    if not isinstance(poem.author, str) or not poem.author.strip():
        raise PoemError("作者不能为空")
    if not isinstance(poem.lines, tuple) or any(
        not isinstance(line, str) for line in poem.lines
    ):
        raise PoemError("诗句必须是字符串元组")
    if not poem.lines:
        raise PoemError("诗至少需要 1 行")
    if len(poem.lines) > MAX_POEM_LINES:
        raise PoemError(f"诗最多 {MAX_POEM_LINES} 行，当前为 {len(poem.lines)} 行")
    for index, line in enumerate(poem.lines, start=1):
        content = line.strip()
        if not content:
            raise PoemError(f"第 {index} 行为空")
        if len(content) > MAX_LINE_CHARS:
            raise PoemError(
                f"第 {index} 行超过 {MAX_LINE_CHARS} 字（当前 {len(content)} 字）"
            )


def _parse_block(block: list[str], index: int) -> Poem:
    """解析以空行分隔的单个诗块，``index`` 从 1 开始计数。"""
    header = block[0]
    if header.count("|") != 1:
        raise PoemError(f"第 {index} 首格式错误：首行应为「标题|作者」")
    title, author = (part.strip() for part in header.split("|"))
    if not title:
        raise PoemError(f"第 {index} 首标题不能为空")
    if not author:
        raise PoemError(f"第 {index} 首作者不能为空")

    lines = tuple(line.strip() for line in block[1:])
    if not lines:
        raise PoemError(f"第 {index} 首《{title}》没有诗句")
    if len(lines) > MAX_POEM_LINES:
        raise PoemError(
            f"第 {index} 首《{title}》最多 {MAX_POEM_LINES} 行，当前为 {len(lines)} 行"
        )
    for line_index, line in enumerate(lines, start=1):
        if "|" in line:
            raise PoemError(f"第 {index} 首第 {line_index} 行不能包含「|」")
        if not line:
            raise PoemError(f"第 {index} 首第 {line_index} 行为空")
        if len(line) > MAX_LINE_CHARS:
            raise PoemError(
                f"第 {index} 首第 {line_index} 行超过 {MAX_LINE_CHARS} 字"
                f"（当前 {len(line)} 字）"
            )

    return Poem(title=title, author=author, lines=lines)


def parse_poem_text(text: str) -> list[Poem]:
    """解析自定义诗稿文本。

    格式为 ``标题|作者`` 一行，随后是若干诗句行，诗与诗之间用空行分隔。
    空文本、缺少分隔符、标题/作者为空、行数或字数越界都会抛出
    :class:`PoemError`。
    """
    if not isinstance(text, str):
        raise PoemError("诗稿内容必须是字符串")

    blocks: list[list[str]] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line:
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)

    if not blocks:
        raise PoemError("诗稿内容为空，至少需要一首古诗")

    return [_parse_block(block, index) for index, block in enumerate(blocks, start=1)]


def read_poems(path: Path) -> list[Poem]:
    """读取诗稿文件，按 UTF-8（含 BOM）优先、GBK 回退的顺序解码。

    文件不存在时抛出 :class:`FileNotFoundError`；两种编码都无法解码时抛出
    :class:`PoemError`。
    """
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"找不到输入文件：{path}") from exc

    for encoding in ("utf-8-sig", "gbk"):
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        return parse_poem_text(text)

    raise PoemError("无法解码诗稿文件，请使用 UTF-8 或 GBK 编码")


def layout_columns(poem: Poem) -> list[list[str]]:
    """把诗句拆成竖排列。

    返回的列表第 0 列位于最右侧，每一列内部的字符自上而下排列；
    标点同样单独占一格。
    """
    validate_poem(poem)
    return [[char for char in line.strip()] for line in poem.lines]


def grid_size_for(poem: Poem, columns_per_page: int = 0) -> tuple[int, int]:
    """返回整首诗的稿纸网格尺寸 ``(列数, 行数)``。

    ``columns_per_page`` 为 0 表示不限列数；大于 0 时按每页列数换行，
    行数按所需的列带数成倍增长。
    """
    validate_poem(poem)
    if isinstance(columns_per_page, bool) or not isinstance(columns_per_page, int):
        raise PoemError("每页列数必须是整数")
    if columns_per_page < 0:
        raise PoemError("每页列数不能为负数")

    columns = len(poem.lines)
    rows = max(len(line.strip()) for line in poem.lines)
    if columns_per_page == 0 or columns <= columns_per_page:
        return columns, rows

    bands = (columns + columns_per_page - 1) // columns_per_page
    return columns_per_page, rows * bands
