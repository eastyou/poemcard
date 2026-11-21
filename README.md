# poemcard

[![CI](https://github.com/eastyou/poemcard/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/poemcard/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)


把古诗排成**竖排（自上而下、自右向左）**的 A4 展示卡与课堂书写稿纸。

- 纯 Python 标准库，零第三方依赖，Python 3.9+
- 逐字 `<text>` 定位生成竖排 SVG，不依赖 CSS `writing-mode`，跨浏览器与打印结果一致
- 内置 12 首公版古诗，支持自定义诗稿文件（UTF-8 / GBK）
- 一键生成展示卡、稿纸格、描红临写页
- 所有文字均经过 HTML 转义，非法输入给出中文错误提示

## 安装

```bash
pip install -e .
```

也可以不安装，直接在仓库根目录运行：

```bash
python3 -m poemcard --help
```

## 快速开始

```bash
# 生成全部内置古诗的展示卡
poemcard -o examples/poems.html --all

# 只生成《静夜思》，并叠加稿纸方格
poemcard -o jingyesi.html --poem 静夜思 --grid

# 生成描红临写页（淡色原诗 + 空白方格）
poemcard -o blank.html --poem 静夜思 --blank

# 读取自定义诗稿
poemcard -i my-poems.txt -o my-cards.html
```

成功时终端输出：

```text
已生成 examples/poems.html（12 首）
```

## 自定义诗稿格式

`标题|作者` 一行，随后是若干诗句行；诗与诗之间用**空行**分隔。

```text
静夜思|李白
床前明月光，
疑是地上霜。
举头望明月，
低头思故乡。

春晓|孟浩然
春眠不觉晓，
处处闻啼鸟。
夜来风雨声，
花落知多少。
```

校验规则：

- 标题、作者不能为空
- 每首 1～8 行，单行 1～20 字（标点计入字数）
- 诗句中不能出现分隔符 `|`
- 文件优先按 UTF-8（含 BOM）解码，失败后回退 GBK

## 命令行参数

| 参数 | 说明 |
| --- | --- |
| `-o, --output` | 输出 HTML 路径，默认 `poemcard.html` |
| `-i, --input` | 读取自定义诗稿文件 |
| `--poem TITLE` | 按标题筛选内置古诗 |
| `--all` | 生成全部内置古诗（默认行为） |
| `--grid` | 在文字下叠加稿纸方格 |
| `--blank` | 生成描红临写页 |
| `--title` | 页面标题，默认「古诗竖排卡」 |

不带 `--poem` 且不带 `--all` 时，默认生成全部内置古诗。

退出码：

- `0`：生成成功
- `1`：文件不存在或写入失败
- `2`：参数非法、诗稿格式错误或编码无法识别（错误信息输出到 stderr）

## Python API

```python
from poemcard import BUILTIN_POEMS, Poem, render_cards, render_guide_blank

# 内置诗
html = render_cards(BUILTIN_POEMS, grid=False, title="三年级古诗展示")

# 自定义诗
poem = Poem(
    title="静夜思",
    author="李白",
    lines=("床前明月光，", "疑是地上霜。", "举头望明月，", "低头思故乡。"),
)
blank_html = render_guide_blank(poem)
```

其他可复用函数：

- `parse_poem_text(text)` / `read_poems(path)`：解析诗稿
- `layout_columns(poem)`：按自右向左拆成竖排列，标点单独占格
- `grid_size_for(poem, columns_per_page=0)`：返回稿纸尺寸 `(列数, 行数)`
- `validate_poem(poem)`：校验单首诗，非法时抛出 `PoemError`

所有非法输入统一抛出 `PoemError`（`ValueError` 的子类）。

## 排版说明

- 页面使用 `@page { size: A4; margin: 0 }`，每页 `210mm × 297mm`，内边距 `12mm`
- 每首诗一页，标题与作者横排居中，诗句逐字定位、自右向左分列
- 字号根据最长列与列数自适应，保证内容不溢出
- 稿纸模式下每个字（含标点）对应一个方格
- 临写页使用淡色原诗，并在最左侧额外留出一列空白格
- 字体回退：`"Kaiti SC", "STKaiti", "KaiTi", serif`

## 开发与测试

```bash
python3 -m unittest discover -s tests -v
```

示例产物：

- `examples/poems.html`：全部内置古诗的展示卡
- `examples/poems-blank.html`：全部内置古诗的描红临写册

## 目录结构

```text
poemcard/
├── poemcard/
│   ├── __init__.py
│   ├── __main__.py
│   ├── model.py      # 数据模型、内置诗、解析与校验
│   ├── render.py     # A4 HTML / SVG 渲染
│   └── cli.py        # 命令行入口
├── tests/
│   ├── test_model.py
│   ├── test_render.py
│   └── test_cli.py
├── examples/
├── pyproject.toml
├── LICENSE
└── README.md
```

## License

MIT © 2026 eastyou
