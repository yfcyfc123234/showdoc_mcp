# 通用个人 MCP 服务器

整合多个功能模块的通用个人 MCP 服务器，支持持续添加新功能。

## 快速开始：在 Cursor 中使用 MCP

### 1. 安装项目

```bash
# 在项目根目录执行（开发模式安装）
pip install -e .
```

### 2. 配置 MCP 服务器

在任意项目的 `.cursor/mcp.json` 文件中添加以下配置：

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

### 3. 重启 Cursor

配置完成后，重启 Cursor 即可使用所有 MCP 工具。

### 4. 可用工具

#### ShowDoc 相关工具

- `fetch_showdoc_apis` - 从 ShowDoc 抓取接口树
- `fetch_showdoc_node_tree` - 抓取轻量级节点树
- `generate_android_from_showdoc` - 一键从 ShowDoc 生成 Android 代码
- `generate_flutter_from_showdoc` - 一键从 ShowDoc 生成 Flutter 代码
- `fetch_node_detail_info` - 查询指定节点详细信息
- `fetch_node_cookie` - 查询指定节点的 Cookie 信息

#### Cursor Cloud Agents API 工具

- `set_cursor_api_key_tool` - 设置并缓存 Cursor API Key（首次使用必需）
- `list_cursor_agents_tool` - 列出所有云端代理
- `get_cursor_agent_status_tool` - 获取代理状态
- `get_cursor_agent_conversation_tool` - 获取代理会话历史
- `add_cursor_agent_followup_tool` - 为代理添加跟进指令
- `delete_cursor_agent_tool` - 删除代理
- `get_cursor_api_key_info_tool` - 获取 API Key 信息
- `list_cursor_models_tool` - 列出推荐模型
- `list_cursor_repositories_tool` - 列出 GitHub 仓库

### 5. 使用示例

#### 首次使用 Cursor Agents API

```json
{
  "api_key": "your_cursor_api_key_here",
  "fetch_user_info": true
}
```

调用工具：`set_cursor_api_key_tool`

#### 从 ShowDoc 生成 Android 代码

```json
{
  "base_url": "https://doc.cqfengli.com/web/#/90/",
  "password": "123456",
  "node_name": "订单",
  "base_package": "com.example.api",
  "output_dir": "android_output"
}
```

调用工具：`generate_android_from_showdoc`

更多使用示例和详细说明，请查看 [mcp_server/README.md](mcp_server/README.md)

---

## 项目结构

```text
showdoc/
├── core/                   # 核心模块：ShowDoc 客户端、验证码识别
├── android_codegen/        # Android 代码生成工具（Entity、Repository、Retrofit）
├── flutter_codegen/        # Flutter 代码生成工具
├── cursor_agents/         # Cursor Cloud Agents API 客户端
├── mcp_server/            # MCP 服务器实现
├── api_docs/              # API 文档示例和预研文档
└── pyproject.toml         # 项目配置
```

## 核心功能

### 1. ShowDoc 数据获取和代码生成

#### ShowDoc 数据获取 (`core/`)

- 自动登录（支持密码或 Cookie 认证）
- Cookie 自动保存和复用（类似浏览器会话管理）
- 验证码识别（基于 ddddocr，识别准确率高）
- 结构化数据解析（分类、页面、API 定义）
- 支持按节点筛选数据
- 支持多种 URL 格式（标准、登录页、`https://www.showdoc.com.cn/{item}/{page}` 等共享链接）

#### 代码生成

- **Android** (`android_codegen/`): Entity 实体类、Repository 数据仓库、Retrofit 接口、OkHttp 配置
- **Flutter** (`flutter_codegen/`): Entity 实体类、Repository 数据仓库、Dio Service 接口、Dio 配置

### 2. Cursor Cloud Agents API (`cursor_agents/`)

- 动态 API Key 管理和自动缓存
- 完整的 Cursor Cloud Agents API 封装
- 支持代理管理、会话查询、跟进指令等功能

### 3. MCP 服务器 (`mcp_server/`)

提供统一的 MCP 协议接口，整合所有功能模块：

- ShowDoc 相关工具（抓取、代码生成等）
- Cursor Agents 相关工具（代理管理、会话查询等）
- 持续扩展中...

## 开发使用

### 安装依赖

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或安装完整项目（包括 MCP 服务器）
pip install -e .
```

### Python 代码使用示例

```python
from core import ShowDocClient

# 初始化客户端
base_url = "https://doc.cqfengli.com/web/#/90/"
client = ShowDocClient(base_url, password="123456")

# 获取所有接口数据
api_tree = client.get_all_apis()

# 获取指定节点的数据
api_tree = client.get_all_apis(node_name="订单")

# 转换为字典格式
data = api_tree.to_dict()
```

### 运行测试

```bash
# 运行核心模块测试
python -m core.test

# 运行 Cursor Agents API 测试
python -m cursor_agents.test

# 运行 Flutter 代码生成测试
python -m flutter_codegen.test
```

## 模块说明

- **core/**: ShowDoc 客户端核心实现，详见 [core/README.md](core/README.md)

- **android_codegen/**: Android 代码生成工具，详见 [android_codegen/README.md](android_codegen/README.md)
- **flutter_codegen/**: Flutter 代码生成工具，详见 [flutter_codegen/README.md](flutter_codegen/README.md)
- **cursor_agents/**: Cursor Cloud Agents API 客户端，详见 [cursor_agents/README.md](cursor_agents/README.md)
- **mcp_server/**: MCP 服务器，详见 [mcp_server/README.md](mcp_server/README.md)
- **api_docs/**: API 文档示例，详见 [api_docs/README.md](api_docs/README.md)
- **archive_tools/**: 通用压缩/解压工具模块（ZIP/7Z/RAR），并封装为 MCP 工具，详见 [archive_tools/README.md](archive_tools/README.md)

## 依赖要求

- Python >= 3.9

- 核心依赖：requests, opencv-python, numpy, ddddocr

## 开发规范

本项目遵循以下规范：

- 使用简体中文进行注释和文档
- 优先使用现代 Python 特性（类型注解、dataclass 等）
- 模块化设计，保持单一职责
- 详细的异常处理和错误提示

## 许可证

本项目为内部工具，仅供团队使用。
