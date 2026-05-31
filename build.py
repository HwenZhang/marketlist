#!/usr/bin/env python3
"""把 secondhand_items_free.md 的物品表同步进 index.html 的 ITEMS 列表。

用法：
    python3 build.py
然后照常 git add -A && git commit -m "..." && git push

说明：
- 唯一需要手动编辑的就是 secondhand_items_free.md（熟悉的 markdown 表格）。
- 真实价格（标价备份）会按物品名称从现有 index.html 自动保留，不会被覆盖成 0。
- 新增的物品价格默认取 md 里的值（一般是 0）。
"""
import re
import sys
import pathlib

MD = pathlib.Path("secondhand_items_free.md")
HTML = pathlib.Path("index.html")


def parse_md(text):
    items = []
    cat = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("## "):
            cat = line[3:].strip()
            continue
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        name, price, link, img, ship = cells[:5]
        if name == "物品" or set(name) <= set("-: "):
            continue  # 跳过表头行与 |---| 分隔行
        m = re.search(r"\((https?://[^)]+)\)", link)
        link_url = m.group(1) if m else ""
        m = re.search(r"!\[[^\]]*\]\(([^)]+)\)", img)
        img_path = m.group(1) if m else ""
        if img_path.startswith("./"):
            img_path = img_path[2:]
        items.append({"cat": cat, "name": name, "price": price,
                      "link": link_url, "img": img_path, "ship": ship})
    return items


def existing_prices(html):
    prices = {}
    for m in re.finditer(r'name:"((?:[^"\\]|\\.)*)",\s*price:"([^"]*)"', html):
        prices[m.group(1)] = m.group(2)
    return prices


def js(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def gen_block(items, prices):
    out = ["  /* ITEMS_START — 由 build.py 从 secondhand_items_free.md 自动生成，勿手改 */",
           "  const ITEMS = ["]
    last = None
    for it in items:
        if it["cat"] != last:
            out.append(f'    // ---------- {it["cat"]} ----------')
            last = it["cat"]
        price = prices.get(it["name"], it["price"] or "0")
        out.append("    {{ cat:{}, name:{}, price:{}, link:{}, img:{}, ship:{} }},".format(
            js(it["cat"]), js(it["name"]), js(price), js(it["link"]), js(it["img"]), js(it["ship"])))
    out += ["  ];", "  /* ITEMS_END */"]
    return "\n".join(out)


def main():
    if not MD.exists() or not HTML.exists():
        sys.exit("✗ 找不到 secondhand_items_free.md 或 index.html（请在项目根目录运行）。")
    html = HTML.read_text(encoding="utf-8")
    items = parse_md(MD.read_text(encoding="utf-8"))
    if not items:
        sys.exit("✗ 没从 md 里解析到任何物品，已中止。")
    prices = existing_prices(html)
    block = gen_block(items, prices)
    new_html, n = re.subn(r"  /\* ITEMS_START.*?/\* ITEMS_END \*/",
                          lambda _: block, html, count=1, flags=re.S)
    if n != 1:
        sys.exit("✗ 没找到 index.html 里的 ITEMS_START/END 标记区块，未修改。")
    HTML.write_text(new_html, encoding="utf-8")
    added = [it["name"] for it in items if it["name"] not in prices]
    print(f"✓ 已同步 {len(items)} 件物品到 index.html。")
    if added:
        print("  新增：" + "、".join(added))
    print("  接着运行： git add -A && git commit -m \"update list\" && git push")


if __name__ == "__main__":
    main()
