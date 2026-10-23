# OneNote CLI

> 命令行读取本地 OneNote 笔记本（只读：`list` / `read` / `search` / `tree` / `info`）。

## 说明

Windows only，依赖 Microsoft Office OneNote Desktop 的 Interop 接口（`Microsoft.Office.Interop.OneNote`）。

> ⚠️ 当前仅支持**读取**笔记本/页面内容，尚未实现创建、更新、删除页面等写入操作。

## 使用

```powershell
python onenote_cli.py --help
# 或通过 onenote.bat 调用
```

输出 JSON，便于脚本与 AI 工具集成。
