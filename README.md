# zhaowen-cli

个人自用的命令行小工具集：每个工具一个子目录，独立可用、独立成篇。

| 工具 | 目录 | 说明 |
|---|---|---|
| OneNote CLI | [`onenote-cli/`](onenote-cli/) | 命令行读取本地 OneNote 笔记本（只读：`list` / `read` / `search` / `tree` / `info`），Windows + Office Interop |
| winotes-cli | [`winnote-cli/`](winnote-cli/) | Windows 便签的命令行接口（JSON 输出，AI 友好），PyPI 已发布 `winotes-cli` |
| 智能体对话管理 | [`agent-dialog-management/`](agent-dialog-management/) | 统一管理本机 Claude Code / Codex 对话记录：查找、查看、导出与一键恢复会话（含 SKILL.md，可作 skill 挂载） |

## 收录说明

- 2026-10 由 `OneNote-cli`、`winnote-cli`、`agent-dialog_management` 三库合并而成，**各自 git 历史完整保留**（`git log -- onenote-cli/` 等可查全部原始提交）。
- `qchat-cli`、`server_manager` 保持独立仓库，不在本合集。
- 后续新增小工具按同样模式追加子目录。
