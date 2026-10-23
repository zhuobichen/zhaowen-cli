#!/usr/bin/env python3
"""
OneNote CLI - 命令行直接读写本地 OneNote 笔记本。
Windows only, requires Microsoft Office OneNote Desktop.
"""

import argparse
import json
import sys
import os

import clr
import System

_INTEROP_DLL = os.path.join(
    os.environ.get("SystemRoot", r"C:\Windows"),
    r"assembly\GAC_MSIL\Microsoft.Office.Interop.OneNote"
    r"\15.0.0.0__71e9bce111e9429c\Microsoft.Office.Interop.OneNote.dll",
)

_onenote = None
_hs_enum = None
_pi_enum = None


def _init():
    global _onenote, _hs_enum, _pi_enum
    if _onenote:
        return
    if not os.path.exists(_INTEROP_DLL):
        print("错误: 未安装 Microsoft Office OneNote Desktop", file=sys.stderr)
        sys.exit(1)
    asm = System.Reflection.Assembly.LoadFile(_INTEROP_DLL)
    _hs_enum = asm.GetType("Microsoft.Office.Interop.OneNote.HierarchyScope")
    _pi_enum = asm.GetType("Microsoft.Office.Interop.OneNote.PageInfo")
    app_type = asm.GetType("Microsoft.Office.Interop.OneNote.ApplicationClass")
    _onenote = System.Activator.CreateInstance(app_type)


def _hs(name: str):
    return System.Enum.Parse(_hs_enum, name)


def _pi(name: str):
    return System.Enum.Parse(_pi_enum, name)


def hierarchy_xml(node_id: str, scope: str) -> str:
    result = _onenote.GetHierarchy(node_id, _hs(scope), None)
    return result or ""


def page_content_xml(page_id: str) -> str:
    result = _onenote.GetPageContent(page_id, None, _pi("piAll"))
    return result or ""


def _extract_text(xml: str) -> str:
    """从 OneNote 页面 XML 提取纯文本"""
    from lxml import etree
    ns = "{http://schemas.microsoft.com/office/onenote/2013/onenote}"
    try:
        root = etree.fromstring(xml.encode("utf-8"))
        lines = [t.text for t in root.iter(ns + "T") if t.text]
        return "\n".join(lines) if lines else "(空页面)"
    except Exception:
        return xml


# -------- Commands --------

def cmd_list(args):
    """列出笔记本 / 分区 / 页面"""
    _init()
    from lxml import etree
    ns = "{http://schemas.microsoft.com/office/onenote/2013/onenote}"

    if args.type == "notebooks":
        xml = hierarchy_xml("", "hsNotebooks")
        root = etree.fromstring(xml.encode("utf-8"))
        rows = [[nb.attrib.get("name", ""), nb.attrib.get("ID", ""),
                 nb.attrib.get("lastModifiedTime", "")[:10]]
                for nb in root.iter(ns + "Notebook")]
        _print_table(["名称", "ID", "最后修改"], rows)

    elif args.type == "sections":
        xml = hierarchy_xml(args.parent_id, "hsSections")
        root = etree.fromstring(xml.encode("utf-8"))
        rows = [[sec.attrib.get("name", ""), sec.attrib.get("ID", ""),
                 sec.attrib.get("lastModifiedTime", "")[:10]]
                for sec in root.iter(ns + "Section")]
        _print_table(["名称", "ID", "最后修改"], rows)

    elif args.type == "pages":
        xml = hierarchy_xml(args.parent_id, "hsPages")
        root = etree.fromstring(xml.encode("utf-8"))
        rows = []
        for page in root.iter(ns + "Page"):
            level = int(page.attrib.get("pageLevel", "1"))
            prefix = "  " * (level - 1)
            rows.append([prefix + page.attrib.get("name", ""),
                         page.attrib.get("ID", ""),
                         page.attrib.get("lastModifiedTime", "")[:10]])
        _print_table(["名称", "ID", "最后修改"], rows)


def cmd_read(args):
    """读取页面内容"""
    _init()
    xml = page_content_xml(args.page_id)
    if args.format == "xml":
        print(xml)
    else:
        print(_extract_text(xml))


def cmd_search(args):
    """按标题搜索页面"""
    results = _do_search(args.keyword, args.limit)
    if not results:
        print(f"未找到匹配 '{args.keyword}' 的页面")
        return

    rows = [[r["page_name"][:60], r["section"], r["notebook"],
             r["modified"], r["page_id"]] for r in results]
    _print_table(["页面", "分区", "笔记本", "修改日期", "ID"], rows)

    if args.json:
        print("\n--- JSON ---")
        print(json.dumps(results, ensure_ascii=False, indent=2))


def cmd_sr(args):
    """搜索并读取第一个匹配页面的内容"""
    results = _do_search(args.keyword, args.limit)
    if not results:
        print(f"未找到匹配 '{args.keyword}' 的页面")
        return

    print(f"找到 {len(results)} 个匹配页面\n")
    top = results[0]
    print(f">>> [{top['notebook']}] > [{top['section']}] > {top['page_name']}")
    print(f"    ID: {top['page_id']}")
    print(f"    修改: {top['modified']}\n")

    xml = page_content_xml(top["page_id"])
    print(_extract_text(xml))


def cmd_tree(args):
    """打印完整层次结构树"""
    _init()
    from lxml import etree
    ns = "{http://schemas.microsoft.com/office/onenote/2013/onenote}"

    nb_xml = hierarchy_xml("", "hsNotebooks")
    nb_root = etree.fromstring(nb_xml.encode("utf-8"))
    result = []

    for nb in nb_root.iter(ns + "Notebook"):
        nb_info = {
            "name": nb.attrib.get("name", ""),
            "id": nb.attrib.get("ID", ""),
            "path": nb.attrib.get("path", ""),
            "modified": nb.attrib.get("lastModifiedTime", "")[:10],
            "sections": [],
        }
        sec_xml = hierarchy_xml(nb.attrib.get("ID", ""), "hsSections")
        sec_root = etree.fromstring(sec_xml.encode("utf-8"))
        for sec in sec_root.iter(ns + "Section"):
            sec_info = {
                "name": sec.attrib.get("name", ""),
                "id": sec.attrib.get("ID", ""),
                "modified": sec.attrib.get("lastModifiedTime", "")[:10],
                "pages": [],
            }
            page_xml = hierarchy_xml(sec.attrib.get("ID", ""), "hsPages")
            page_root = etree.fromstring(page_xml.encode("utf-8"))
            for page in page_root.iter(ns + "Page"):
                sec_info["pages"].append({
                    "name": page.attrib.get("name", ""),
                    "id": page.attrib.get("ID", ""),
                    "level": page.attrib.get("pageLevel", "1"),
                    "modified": page.attrib.get("lastModifiedTime", "")[:10],
                })
            nb_info["sections"].append(sec_info)
        result.append(nb_info)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # Text tree
    for nb in result:
        print(f"\n[{nb['name']}]  ({nb['modified']})")
        for i, sec in enumerate(nb["sections"]):
            last_sec = i == len(nb["sections"]) - 1
            prefix = "\\-- " if last_sec else "+-- "
            print(f"{prefix}[{sec['name']}] ({len(sec['pages'])} pages, {sec['modified']})")
            child_prefix = "    " if last_sec else "|   "
            for j, page in enumerate(sec["pages"]):
                last_page = j == len(sec["pages"]) - 1
                p_prefix = child_prefix + ("\\-- " if last_page else "|-- ")
                print(f"{p_prefix}{page['name']} ({page['modified']})")


def cmd_info(args):
    """显示统计信息"""
    _init()
    from lxml import etree
    ns = "{http://schemas.microsoft.com/office/onenote/2013/onenote}"

    nb_xml = hierarchy_xml("", "hsNotebooks")
    root = etree.fromstring(nb_xml.encode("utf-8"))
    nb_list = list(root.iter(ns + "Notebook"))

    total_pages = 0
    total_sections = 0
    for nb in nb_list:
        sec_xml = hierarchy_xml(nb.attrib.get("ID", ""), "hsSections")
        sec_root = etree.fromstring(sec_xml.encode("utf-8"))
        for sec in sec_root.iter(ns + "Section"):
            total_sections += 1
            page_xml = hierarchy_xml(sec.attrib.get("ID", ""), "hsPages")
            page_root = etree.fromstring(page_xml.encode("utf-8"))
            total_pages += len(list(page_root.iter(ns + "Page")))

    print(f"笔记本: {len(nb_list)} 个")
    print(f"分区:   {total_sections} 个")
    print(f"页面:   {total_pages} 个")
    print(f"引擎:   Microsoft.Office.Interop.OneNote (.NET)")


def _do_search(keyword: str, limit: int = None) -> list:
    """搜索页面，返回结果列表"""
    _init()
    from lxml import etree
    ns = "{http://schemas.microsoft.com/office/onenote/2013/onenote}"

    keyword = keyword.lower()
    results = []

    nb_xml = hierarchy_xml("", "hsNotebooks")
    nb_root = etree.fromstring(nb_xml.encode("utf-8"))
    for nb in nb_root.iter(ns + "Notebook"):
        sec_xml = hierarchy_xml(nb.attrib.get("ID", ""), "hsSections")
        sec_root = etree.fromstring(sec_xml.encode("utf-8"))
        for sec in sec_root.iter(ns + "Section"):
            page_xml = hierarchy_xml(sec.attrib.get("ID", ""), "hsPages")
            page_root = etree.fromstring(page_xml.encode("utf-8"))
            for page in page_root.iter(ns + "Page"):
                page_name = page.attrib.get("name", "")
                if keyword in page_name.lower():
                    results.append({
                        "page_id": page.attrib.get("ID", ""),
                        "page_name": page_name,
                        "section": sec.attrib.get("name", ""),
                        "notebook": nb.attrib.get("name", ""),
                        "modified": page.attrib.get("lastModifiedTime", "")[:10],
                    })

    if limit:
        results = results[:int(limit)]
    return results


def _print_table(headers: list, rows: list):
    """打印对齐表格"""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    for i, h in enumerate(headers):
        if h == "ID":
            widths[i] = min(widths[i], 50)

    fmt = "  ".join(f"{{{i}:<{w}}}" for i, w in enumerate(widths))
    print(fmt.format(*headers))
    print("-" * (sum(widths) + 2 * (len(headers) - 1)))
    for row in rows:
        display = []
        for i, cell in enumerate(row):
            s = str(cell)
            if headers[i] == "ID" and len(s) > 50:
                s = s[:47] + "..."
            display.append(s[:widths[i]])
        print(fmt.format(*display))


def main():
    parser = argparse.ArgumentParser(
        prog="onenote",
        description="本地 OneNote CLI - 命令行读写 OneNote 笔记本",
    )
    sub = parser.add_subparsers(dest="command", help="子命令")

    p_list = sub.add_parser("list", help="列出笔记本/分区/页面")
    p_list.add_argument("type", choices=["notebooks", "sections", "pages"],
                        help="notebooks | sections | pages")
    p_list.add_argument("parent_id", nargs="?", default="",
                        help="父节点 ID (sections 需要 notebook_id, pages 需要 section_id)")

    p_read = sub.add_parser("read", help="读取页面内容")
    p_read.add_argument("page_id", help="页面 ID")
    p_read.add_argument("-f", "--format", choices=["text", "xml"], default="text",
                        help="text | xml (默认: text)")

    p_search = sub.add_parser("search", help="按标题搜索页面")
    p_search.add_argument("keyword", help="搜索关键词")
    p_search.add_argument("-n", "--limit", type=int, help="限制结果数量")
    p_search.add_argument("--json", action="store_true", help="同时输出 JSON")

    p_sr = sub.add_parser("sr", help="搜索并读取第一个匹配页面的内容")
    p_sr.add_argument("keyword", help="搜索关键词")
    p_sr.add_argument("-n", "--limit", type=int, help="限制搜索数量")

    p_tree = sub.add_parser("tree", help="打印完整笔记本层次树")
    p_tree.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    sub.add_parser("info", help="显示笔记本统计信息")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return

    {
        "list": cmd_list, "read": cmd_read, "search": cmd_search,
        "sr": cmd_sr, "tree": cmd_tree, "info": cmd_info,
    }[args.command](args)


if __name__ == "__main__":
    main()
