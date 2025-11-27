# MCP：ShowDoc → Android 代码生成工具集

本目录用于**功能整合 + MCP 封装**，把现有两个核心能力通过 MCP 暴露出来：

- **a. ShowDoc 抓取**：使用 `core.ShowDocClient` 把 ShowDoc 项目的接口树拉下来；
- **b. 基于 a 的 Android 代码生成**：使用 `android_codegen.AndroidCodeGenerator` 生成 Kotlin 实体类、Retrofit Service、OkHttp 配置等；
- **c. 辅助工具**：打开 / 返回当前 Android 输出目录，方便上层 IDE 或工具跳转。

所有实现都 **尽量复用现有代码，不重复造轮子**。

---

## 工具一：`showdoc_fetch_apis`

- **用途**：从 ShowDoc 拉取接口定义，输出为结构化 JSON，可直接作为后续代码生成的输入或快照文件。
- **实现复用**：
  - 直接调用 `core.ShowDocClient(base_url, cookie).get_all_apis(node_name=...)`；
  - 使用 `ApiTree.to_dict()` 转换为 JSON 友好的结构。
- **典型入参**：
  - `base_url: str` —— ShowDoc 项目 URL，支持多种格式：
    - 标准格式：`https://doc.cqfengli.com/web/#/90/`
    - 登录页面格式：`https://doc.cqfengli.com/web/#/item/password/88?page_id=4091`
  - `cookie: Optional[str]` —— 认证 Cookie（可选，如果提供 password 则可不提供）
  - `password: Optional[str]` —— 项目访问密码（可选，默认 "123456"，如果提供 cookie 则可不提供），将自动进行验证码登录
  - `node_name: Optional[str]` —— 可选节点名（分类），`None` / `"全部"` / `"all"` 表示全量
  - `save_path: Optional[str]` —— 可选，本地快照保存路径，例如 `showdoc_export_90.json`

**Cookie 自动管理**：登录成功后的 Cookie 会自动保存到 `.showdoc_cookies.json`，下次运行时自动复用（如果有效且未过期）。
- **典型出参**（JSON 对象）：
  - `api_tree`：`ApiTree.to_dict()` 的结果
  - `snapshot_path`：如果有保存快照，则返回文件路径

---

## 工具二：`android_generate_from_showdoc`

- **用途**：基于工具一的输出或本地快照，生成 Android 侧的 Kotlin 代码。
- **实现复用**：
  - 将 JSON 转换回 `ApiTree` 结构（轻量适配）；
  - 调用 `AndroidCodeGenerator.generate(api_tree, ...)` 完成所有代码生成；
  - 完全沿用当前的增量版本控制逻辑。
- **典型入参**（两种模式至少支持一种，实际实现中两种都支持）：
  - `api_tree_json: Optional[dict]` —— 直接传结构化 JSON（通常来自 `showdoc_fetch_apis` 的 `api_tree` 字段）；
  - `snapshot_path: Optional[str]` —— 传本地 `*.json` 路径，内部读取后再解析；
  - `base_package: str` —— Kotlin 包名，默认可沿用 `android_codegen.test` 中的配置；
  - `output_dir: str` —— 输出目录，默认 `android_output`；
  - `category_filter: Optional[str]` —— 可选，只生成某个分类；
  - `server_base: Optional[str]` —— ShowDoc 服务器根地址，用于在注释中生成文档链接。
- **典型出参**：
  - `services` / `entities` / `config` / `repository`：各类生成文件的绝对路径列表；
  - `version_control`：来自 `generate()` 的版本控制统计信息。

---

## 工具三：`android_open_output_folder`

- **用途**：返回（可选尝试在本机打开）当前 Android 输出目录，方便上层 IDE / MCP 客户端做跳转或文件浏览。
- **实现复用**：
  - 目录策略与 `android_codegen.test` 中 `OUTPUT_DIR` / `OUTPUT_DIR_CONFIG` 对齐；
  - 不做代码生成，只处理路径和可选的 `os.startfile(...)` / `subprocess` 调用（如有需要可以按平台区分执行方式）。
- **典型入参**：
  - `output_dir: Optional[str]` —— 如果为空则使用默认 `android_output`
  - `open_in_explorer: bool` —— 是否尝试在本机文件管理器中打开。
- **典型出参**：
  - `output_dir: str` —— 实际使用的目录绝对路径；
  - `exists: bool` —— 目录当前是否存在。

---

## 工具四：`showdoc_fetch_and_generate`（一键抓取 + 生成）

- **用途**：你只需要提供 `base_url`、`cookie` 和要生成代码的 `node_name`，就能一键完成 ShowDoc 抓取 + Android 代码生成。
- **实现复用**：
  - 内部先调用 `showdoc_fetch_apis` 抓取接口树；
  - 再调用 `android_generate_from_showdoc` 完成代码生成；
  - 中间可选把快照保存为 JSON 文件。
- **典型入参**：
  - `base_url: str` —— ShowDoc 项目 URL；
  - `cookie: Optional[str]` —— 认证 Cookie（可选，如果提供 password 则可不提供）；
  - `password: Optional[str]` —— 项目访问密码（可选，如果提供 cookie 则可不提供），将自动进行验证码登录；
  - `node_name: Optional[str]` —— 要生成代码的 API 节点名称（分类），`None` / `"全部"` / `"all"` 表示全量；
  - `base_package: str` —— Kotlin 包名，默认 `com.example.api`；
  - `output_dir: Optional[str]` —— 输出目录，默认 `android_output`；
  - `server_base: Optional[str]` —— ShowDoc 服务器根地址（不传则从 `base_url` 自动推断）；
  - `save_snapshot_path: Optional[str]` —— 可选，抓取结果快照保存路径。
- **典型出参**：
  - `ok: bool` —— 是否全部成功；
  - `stage: Optional[str]` —— 出错阶段（`"fetch"` / `"generate"` / `None`）；
  - `snapshot_path: Optional[str]` —— 如有保存快照则返回路径；
  - `output_dir: Optional[str]` —— 实际生成代码的目录；
  - `generated: Optional[dict]` —— 生成代码的详细信息（来自 `AndroidCodeGenerator.generate`）。

### 直接在代码里使用示例

```python
from mcp_showdoc_android import showdoc_fetch_and_generate

BASE_URL = "https://doc.cqfengli.com/web/#/90/"
NODE_NAME = "订单"  # 或 None 表示全部

# 方式 1：使用 Cookie
result = showdoc_fetch_and_generate(
    base_url=BASE_URL,
    cookie="think_language=zh-CN; PHPSESSID=xxx",
    node_name=NODE_NAME,
    base_package="com.example.api",
    output_dir="android_output",
    save_snapshot_path="showdoc_export_90.json",
)

# 方式 2：使用密码自动登录（推荐，默认密码 123456）
result = showdoc_fetch_and_generate(
    base_url=BASE_URL,
    password="123456",  # 默认密码，可省略
    node_name=NODE_NAME,
    base_package="com.example.api",
    output_dir="android_output",
    save_snapshot_path="showdoc_export_90.json",
)

if result["ok"]:
    print("生成成功，输出目录：", result["output_dir"])
else:
    print("生成失败，阶段:", result.get("stage"), "错误:", result.get("error"))
```

---

## MCP 服务器：`showdoc-android-mcp`

我们在 `mcp_showdoc_android/mcp_server.py` 中使用 **FastMCP** 实现了一个标准 MCP stdio 服务，专门暴露两个工具：

- `fetch_showdoc_apis`（对应 Python 函数 `showdoc_fetch_apis`）
- `generate_android_from_showdoc`（对应 `showdoc_fetch_and_generate`，支持 `auto_delete_orphaned` 参数）

启动命令（已经在 `pyproject.toml` 注册）：

```bash
showdoc-android-mcp
```

该命令会自动处理 MCP 协议中的 `initialize` / `tools/list` / `tools/call`，因此 Cursor 只要按照 MCP 规范与之通信，就能直接调用上述两个工具。

---

## 在 Cursor 中使用示例（配置 MCP）

- **方式 A（推荐，用于复用 / 发给同事 / CI 部署）：先安装为包，再在任意项目中作为 MCP 使用**

1. 在本项目根目录执行一次（开发模式安装）：

```bash
pip install -e .
```

1. 在任意项目的 `.cursor/mcp.json` 中加入：

```json
{
  "mcpServers": {
    "showdoc-android-mcp": {
      "command": "showdoc-android-mcp",
      "args": [],
      "cwd": ".",
      "env": {
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

- 这样 Cursor 会直接通过全局命令 `showdoc-android-mcp` 启动 MCP 服务，当前项目目录不必是源码所在目录。

---

## 在 Cursor 里调用的参数示例（重点）

- 调用 MCP 工具 `generate_android_from_showdoc` 时，推荐参数：

**方式 1：使用 Cookie（传统方式）**
```json
{
  "base_url": "https://doc.cqfengli.com/web/#/90/",
  "cookie": "think_language=zh-CN; PHPSESSID=xxx",
  "node_name": "订单",              // 或 null 表示全部
  "base_package": "com.example.api",
  "output_dir": "android_output",   // 生成的 Kotlin 代码目录
  "auto_delete_orphaned": false     // 是否自动删除已孤立/待删除旧文件（默认 false）
}
```

**方式 2：使用密码自动登录（推荐，默认密码 123456）**
```json
{
  "base_url": "https://doc.cqfengli.com/web/#/90/",
  "password": "123456",             // 默认密码，可省略，将自动进行验证码登录
  "node_name": "订单",              // 或 null 表示全部
  "base_package": "com.example.api",
  "output_dir": "android_output",
  "auto_delete_orphaned": false
}
```

**注意**：`cookie` 和 `password` 二选一即可，如果都提供则优先使用 `cookie`。

- 整体流程：
  1. Cursor 通过 `showdoc-android-mcp` 启动 MCP 服务；
  1. 你在对话里选择工具 `generate_android_from_showdoc` 并填入上面的参数；
  1. MCP 内部调用 `showdoc_fetch_and_generate`：先抓取 ShowDoc，再生成 Android 代码到 `output_dir`；
  1. 结果以 JSON 返回，包括生成的文件列表和版本控制信息。
