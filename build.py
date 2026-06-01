#!/usr/bin/env python3
"""从 secondhand_items_free.md 生成网页数据，并同步出带价格的 markdown。

用法：
    python3 build.py
然后照常 git add -A && git commit -m "..." && git push

设计：
- 你只需要编辑 secondhand_items_free.md（无价格、好编辑）。
- 价格集中维护在下面的 PRICES 表里（只有有价的几件，其余默认 0）。
- 运行后会生成两样：
    * index.html 的 ITEMS（网页数据，含真实价格）
    * secondhand_items.md（带价格的版本，自动生成，勿手改）
- 网页默认显示真实价格；想看免费版在网址后加 ?free=1。
"""
import re
import sys
import pathlib

SRC = pathlib.Path("secondhand_items_free.md")    # ← 唯一需要手动编辑的文件
PRICED_MD = pathlib.Path("secondhand_items.md")   # 自动生成（带价格）
HTML = pathlib.Path("index.html")

# ===== 价格表：有价格的物品写在这里，其余自动按 0 处理 =====
PRICES = {
    "Xbox Series S(512GB) 游戏机 + 一个 Xbox手柄": "50£",
    "LG 4k 显示器": "50£",
    "KOORUI 165Hz, FHD 1080P 显示器": "10£",
    "键盘": "5£",
    "HEAD Ti S6 Titanium 网球拍 + 网球12个": "15£",
    "壁球拍 + 壁球 2 个": "10£",
    "小桌子": "5£",
}
# =========================================================


def default_price(cat):
    return "0" if cat.startswith("书籍") else "0£"


def price_for(name, cat):
    return PRICES.get(name, default_price(cat))


def is_sep(cells):
    return all(c and set(c) <= set("-: ") for c in cells)


def row_cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_items(text):
    items = []
    cat = None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("## "):
            cat = s[3:].strip()
            continue
        if not s.startswith("|"):
            continue
        cells = row_cells(s)
        if len(cells) < 5 or cells[0] == "物品" or is_sep(cells):
            continue
        name, _price, link, img, ship = cells[:5]
        m = re.search(r"\((https?://[^)]+)\)", link)
        link_url = m.group(1) if m else ""
        m = re.search(r"!\[[^\]]*\]\(([^)]+)\)", img)
        img_path = m.group(1) if m else ""
        if img_path.startswith("./"):
            img_path = img_path[2:]
        items.append({"cat": cat, "name": name, "price": price_for(name, cat),
                      "link": link_url, "img": img_path, "ship": ship})
    return items


def make_priced_md(text):
    """把 free md 原文的价格列替换成真实价格，其余原样保留。"""
    out = ["<!-- 自动生成（build.py），勿手改；请编辑 secondhand_items_free.md -->"]
    cat = None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("## "):
            cat = s[3:].strip()
            out.append(line)
            continue
        if s.startswith("|"):
            cells = row_cells(s)
            if len(cells) >= 5 and cells[0] != "物品" and not is_sep(cells):
                cells[1] = price_for(cells[0], cat)
                out.append("| " + " | ".join(cells) + " |")
                continue
        out.append(line)
    return "\n".join(out) + "\n"


def js(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def gen_block(items):
    out = ["  /* ITEMS_START — 由 build.py 从 secondhand_items_free.md 自动生成，勿手改 */",
           "  const ITEMS = ["]
    last = None
    for it in items:
        if it["cat"] != last:
            out.append(f'    // ---------- {it["cat"]} ----------')
            last = it["cat"]
        out.append("    {{ cat:{}, name:{}, price:{}, link:{}, img:{}, ship:{} }},".format(
            js(it["cat"]), js(it["name"]), js(it["price"]),
            js(it["link"]), js(it["img"]), js(it["ship"])))
    out += ["  ];", "  /* ITEMS_END */"]
    return "\n".join(out)


def main():
    if not SRC.exists() or not HTML.exists():
        sys.exit("✗ 找不到 secondhand_items_free.md 或 index.html（请在项目根目录运行）。")
    text = SRC.read_text(encoding="utf-8")
    items = parse_items(text)
    if not items:
        sys.exit("✗ 没从 md 里解析到任何物品，已中止。")

    names = {it["name"] for it in items}
    missing = [k for k in PRICES if k not in names]
    if missing:
        print("⚠ PRICES 里这些名字在 md 中没找到（可能被改名了，价格不会生效）：")
        for k in missing:
            print("   -", k)

    html = HTML.read_text(encoding="utf-8")
    new_html, n = re.subn(r"  /\* ITEMS_START.*?/\* ITEMS_END \*/",
                          lambda _: gen_block(items), html, count=1, flags=re.S)
    if n != 1:
        sys.exit("✗ 没找到 index.html 里的 ITEMS_START/END 标记区块，未修改。")
    HTML.write_text(new_html, encoding="utf-8")
    PRICED_MD.write_text(make_priced_md(text), encoding="utf-8")

    print(f"✓ 已同步 {len(items)} 件物品 → index.html（带价格）")
    print(f"✓ 已生成带价格版本 → {PRICED_MD}")
    print('  接着运行： git add -A && git commit -m "update list" && git push')


if __name__ == "__main__":
    main()
