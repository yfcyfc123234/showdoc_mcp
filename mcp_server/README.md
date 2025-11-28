# 通用个人 MCP 服务器

本目录用于**功能整合 + MCP 封装**，将多个功能模块通过 MCP 协议统一暴露。

## 功能模块

### ShowDoc 相关工具

- **ShowDoc 抓取**：使用 `core.ShowDocClient` 把 ShowDoc 项目的接口树拉下来
- **代码生成**：
  - Android：使用 `android_codegen.AndroidCodeGenerator` 生成 Kotlin 实体类、Retrofit Service、OkHttp 配置等
  - Flutter：使用 `flutter_codegen.FlutterCodeGenerator` 生成 Dart 实体类、Dio Service、Repository 等
- **辅助工具**：打开 / 返回当前输出目录，方便上层 IDE 或工具跳转

### Cursor Cloud Agents API 工具

- **API Key 管理**：设置并缓存 Cursor API Key
- **代理管理**：列出、查询、删除云端代理
- **会话管理**：获取代理会话历史、添加跟进指令
- **信息查询**：获取 API Key 信息、推荐模型列表、GitHub 仓库列表

所有实现都 **尽量复用现有代码，不重复造轮子**。

> **适用范围说明**：ShowDoc 相关工具支持所有标准的 ShowDoc 站点，只要提供正确的 `base_url` 以及对应该站点的 Cookie 或访问密码即可完成抓取与生成，不局限于任何特定组织或域名。

## 输出目录结构

所有输出文件统一管理在 `output/` 目录下：

```
output/
├── .showdoc_cookies.json    # Cookie 缓存文件（自动管理）
├── android_output/          # Android 代码生成目录（默认，可自定义）
│   ├── entities/            # 实体类
│   ├── services/           # Retrofit Service 接口
│   ├── repository/         # Repository 类
│   └── config/             # 配置文件
├── showdoc_snapshots/       # ShowDoc 接口数据快照（自动保存）
│   ├── {item_id}_{item_name}_{timestamp}.json
│   └── ...
└── captcha_debug/          # 验证码调试图片（仅调试时生成）
    └── ...
```

**说明**：
- 所有接口数据会自动保存到 `output/showdoc_snapshots/`，文件名包含项目 ID、名称和时间戳，便于后续分析
- Android 代码默认输出到 `output/android_output/`，可通过 `output_dir` 参数自定义
- 验证码调试图片仅在登录失败时保存，用于排查验证码识别问题

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
    - 官方分享链接：`https://www.showdoc.com.cn/{item}/{page}`（自动提取 `item_id` 与 `page_id`）
  - `cookie: Optional[str]` —— 认证 Cookie（可选，如果提供 password 则可不提供）
  - `password: Optional[str]` —— 项目访问密码（可选，默认 "123456"，如果提供 cookie 则可不提供），将自动进行验证码登录
  - `node_name: Optional[str]` —— 可选节点名（分类），`None` / `"全部"` / `"all"` 表示全量
  - `save_path: Optional[str]` —— 可选，本地快照保存路径，例如 `showdoc_export_90.json`；如果不指定，会自动保存到 `output/showdoc_snapshots/{item_id}_{item_name}_{timestamp}.json`

**Cookie 自动管理**：登录成功后的 Cookie 会自动保存到 `output/.showdoc_cookies.json`，下次运行时自动复用（如果有效且未过期）。
- **典型出参**（JSON 对象）：
  - `api_tree`：`ApiTree.to_dict()` 的结果
  - `snapshot_path`：如果有保存快照，则返回文件路径

---

## 工具二：`showdoc_fetch_node_tree`

- **用途**：仅获取 ShowDoc 的节点树状结构（分类 + 页面基础信息），避免抓取 API 详情导致的数据量过大。
- **实现复用**：
  - 直接调用 `core.ShowDocClient.get_node_tree(node_name=...)`，内置过滤逻辑与完整抓取保持一致；
  - 输出结构中只包含 `cat_id` / `cat_name` / `children` / `pages(page_id + page_title)` 等轻量字段。
- **典型入参**：
  - `base_url: str`
  - `cookie: Optional[str]` 或 `password: Optional[str]`（二选一）
  - `node_name: Optional[str]`
- **典型出参**：
  - `node_tree: {"item_info": {...}, "categories": [...]}` —— 精简后的树状结构，可直接用于节点选择器 UI。

---

## 工具三：`android_generate_from_showdoc`

- **用途**：基于工具一的输出或本地快照，生成 Android 侧的 Kotlin 代码。
- **实现复用**：
  - 将 JSON 转换回 `ApiTree` 结构（轻量适配）；
  - 调用 `AndroidCodeGenerator.generate(api_tree, ...)` 完成所有代码生成；
  - 完全沿用当前的增量版本控制逻辑。
- **典型入参**（两种模式至少支持一种，实际实现中两种都支持）：
  - `api_tree_json: Optional[dict]` —— 直接传结构化 JSON（通常来自 `showdoc_fetch_apis` 的 `api_tree` 字段）；
  - `snapshot_path: Optional[str]` —— 传本地 `*.json` 路径，内部读取后再解析；
  - `base_package: str` —— Kotlin 包名，默认可沿用 `android_codegen.test` 中的配置；
  - `output_dir: str` —— 输出目录，默认 `output/android_output`（可自定义）；
  - `category_filter: Optional[str]` —— 可选，只生成某个分类；
  - `server_base: Optional[str]` —— ShowDoc 服务器根地址，用于在注释中生成文档链接。
- **典型出参**：
  - `services` / `entities` / `config` / `repository`：各类生成文件的绝对路径列表；
  - `version_control`：来自 `generate()` 的版本控制统计信息。

---

## 工具四：`android_open_output_folder`

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

## 工具五：`showdoc_fetch_and_generate`（一键抓取 + 生成）

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
  - `output_dir: Optional[str]` —— 输出目录，默认 `output/android_output`（可自定义）；
  - `server_base: Optional[str]` —— ShowDoc 服务器根地址（不传则从 `base_url` 自动推断）；
  - `save_snapshot_path: Optional[str]` —— 可选，抓取结果快照保存路径；如果不指定，会自动保存到 `output/showdoc_snapshots/`。
- **典型出参**：
  - `ok: bool` —— 是否全部成功；
  - `stage: Optional[str]` —— 出错阶段（`"fetch"` / `"generate"` / `None`）；
  - `snapshot_path: Optional[str]` —— 如有保存快照则返回路径；
  - `output_dir: Optional[str]` —— 实际生成代码的目录；
  - `generated: Optional[dict]` —— 生成代码的详细信息（来自 `AndroidCodeGenerator.generate`）。

### 直接在代码里使用示例

```python
from mcp_showdoc import showdoc_fetch_and_generate

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

## MCP 服务器：`personal-mcp`

我们在 `mcp_server/mcp_server.py` 中使用 **FastMCP** 实现了一个标准 MCP stdio 服务，当前暴露以下工具：

### ShowDoc 相关工具

- `fetch_showdoc_apis` - 从 ShowDoc 抓取接口树
- `fetch_showdoc_node_tree` - 抓取轻量级节点树
- `generate_android_from_showdoc` - 一键从 ShowDoc 生成 Android 代码
- `generate_flutter_from_showdoc` - 一键从 ShowDoc 生成 Flutter 代码
- `fetch_node_detail_info` - 查询指定节点详细信息
- `fetch_node_cookie` - 查询指定节点的 Cookie 信息

### Cursor Cloud Agents API 工具

- `set_cursor_api_key_tool` - 设置并缓存 Cursor API Key
- `list_cursor_agents_tool` - 列出所有云端代理
- `get_cursor_agent_status_tool` - 获取代理状态
- `get_cursor_agent_conversation_tool` - 获取代理会话历史
- `add_cursor_agent_followup_tool` - 为代理添加跟进指令
- `delete_cursor_agent_tool` - 删除代理
- `get_cursor_api_key_info_tool` - 获取 API Key 信息
- `list_cursor_models_tool` - 列出推荐模型
- `list_cursor_repositories_tool` - 列出 GitHub 仓库

启动命令（已经在 `pyproject.toml` 注册）：

```bash
personal-mcp
```

该命令会自动处理 MCP 协议中的 `initialize` / `tools/list` / `tools/call`，因此 Cursor 只要按照 MCP 规范与之通信，就能直接调用上述工具。

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
    "personal-mcp": {
      "command": "personal-mcp",
      "args": [],
      "cwd": ".",
      "env": {
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

- 这样 Cursor 会直接通过全局命令 `personal-mcp` 启动 MCP 服务，当前项目目录不必是源码所在目录。

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
  1. Cursor 通过 `personal-mcp` 启动 MCP 服务；
  1. 你在对话里选择工具 `generate_android_from_showdoc` 并填入上面的参数；
  1. MCP 内部调用 `showdoc_fetch_and_generate`：先抓取 ShowDoc，再生成 Android 代码到 `output_dir`；
  1. 结果以 JSON 返回，包括生成的文件列表和版本控制信息。

---

## Cursor Cloud Agents API 使用示例

### 1. 设置 API Key

首次使用需要设置 API Key（会自动缓存到 `~/.cursor/mcp_cache/api_key.json`），
同时会自动调用 `/v0/me` API 获取用户信息并缓存到 `output/.cursor_api_key_info.json`：

```json
{
  "api_key": "your_cursor_api_key_here",
  "fetch_user_info": true
}
```

**响应示例**：
```json
{
  "ok": true,
  "message": "API Key 已设置并缓存，用户信息已获取并缓存",
  "user_info": {
    "apiKeyName": "Production API Key",
    "createdAt": "2024-01-15T10:30:00Z",
    "userEmail": "developer@example.com"
  }
}
```

调用工具：`set_cursor_api_key_tool`

**注意**：
- `fetch_user_info` 参数默认为 `true`，首次设置时建议保持默认值
- 用户信息（API Key 名称、创建时间、用户邮箱）会自动缓存，后续可直接读取

### 2. 列出所有代理

```json
{
  "limit": 20,
  "cursor": null
}
```

调用工具：`list_cursor_agents_tool`

### 3. 获取代理状态

```json
{
  "agent_id": "bc_abc123"
}
```

调用工具：`get_cursor_agent_status_tool`

### 4. 获取代理会话

```json
{
  "agent_id": "bc_abc123"
}
```

调用工具：`get_cursor_agent_conversation_tool`

### 5. 添加跟进指令

```json
{
  "agent_id": "bc_abc123",
  "text": "Also add a section about troubleshooting"
}
```

调用工具：`add_cursor_agent_followup_tool`

**注意**：
- 所有 Cursor Agents 工具都支持可选的 `api_key` 参数，用于临时指定不同的 API Key（不会缓存）
- 如果不提供 `api_key` 参数，将自动使用缓存的 API Key
- API Key 缓存位置：`~/.cursor/mcp_cache/api_key.json`
