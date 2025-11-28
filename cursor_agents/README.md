# Cursor Cloud Agents API 模块

Cursor Cloud Agents API 的 Python 客户端封装，支持动态 API Key 管理和自动缓存。

## 功能特性

- **动态 API Key 管理**：支持运行时设置和更新 API Key
- **自动缓存**：API Key 自动保存到本地，下次使用时无需重复设置
- **完整 API 支持**：封装所有 Cursor Cloud Agents API 端点
- **错误处理**：完善的异常处理和错误提示

## API Key 管理

### 缓存位置

- **API Key 缓存**：`~/.cursor/mcp_cache/api_key.json`
- **用户信息缓存**：`output/.cursor_api_key_info.json`（项目根目录下的 output 目录）

### 使用方式

```python
from cursor_agents import CursorAgentsClient

# 方式 1：首次使用，设置 API Key（会自动缓存，并获取用户信息）
client = CursorAgentsClient()
result = client.set_api_key("your_api_key_here", fetch_user_info=True)
# result 包含：
# {
#     "ok": True,
#     "message": "API Key 已设置并缓存，用户信息已获取并缓存",
#     "user_info": {
#         "apiKeyName": "Production API Key",
#         "createdAt": "2024-01-15T10:30:00Z",
#         "userEmail": "developer@example.com"
#     }
# }

# 方式 2：后续使用，自动从缓存加载
client = CursorAgentsClient()

# 方式 3：获取缓存的用户信息
user_info = client.get_cached_user_info()
# 返回：{"apiKeyName": "...", "createdAt": "...", "userEmail": "..."}

# 方式 4：临时使用不同的 API Key（不缓存）
client = CursorAgentsClient(api_key="temporary_key")
```

### 用户信息自动获取

首次设置 API Key 时，会自动调用 `/v0/me` API 获取以下信息：
- `apiKeyName`: API Key 名称
- `createdAt`: 创建时间
- `userEmail`: 用户邮箱

这些信息会缓存到 `output/.cursor_api_key_info.json`，后续可以直接读取，无需重复调用 API。

## API 端点

### 1. 列出代理

```python
result = client.list_agents(limit=20, cursor=None)
# 返回: {"agents": [...], "nextCursor": "..."}
```

### 2. 获取代理状态

```python
result = client.get_agent_status(agent_id="bc_abc123")
# 返回: {"id": "...", "name": "...", "status": "...", ...}
```

### 3. 获取代理会话

```python
result = client.get_agent_conversation(agent_id="bc_abc123")
# 返回: {"id": "...", "messages": [...]}
```

### 4. 添加跟进

```python
result = client.add_followup(
    agent_id="bc_abc123",
    text="Also add a section about troubleshooting",
    images=None  # 可选，最多 5 张图片
)
```

### 5. 删除代理

```python
result = client.delete_agent(agent_id="bc_abc123")
# 返回: {"id": "bc_abc123"}
```

### 6. 获取 API Key 信息

```python
result = client.get_api_key_info()
# 返回: {"apiKeyName": "...", "createdAt": "...", "userEmail": "..."}
```

### 7. 列出模型

```python
result = client.list_models()
# 返回: {"models": ["claude-4-sonnet-thinking", "o3", ...]}
```

### 8. 列出 GitHub 仓库

```python
result = client.list_repositories()
# 返回: {"repositories": [{"owner": "...", "name": "...", ...}, ...]}
```

**注意**：此端点有严格的速率限制（1 次/用户/分钟，30 次/用户/小时）

## 错误处理

```python
from cursor_agents import CursorAgentsClient

try:
    client = CursorAgentsClient()
    result = client.list_agents()
except ValueError as e:
    # API Key 未设置或无效
    print(f"API Key 错误: {e}")
except RuntimeError as e:
    # 网络请求失败
    print(f"请求失败: {e}")
```

## 获取 API Key

1. 访问 [Cursor 设置页面](https://cursor.com/settings)
2. 找到 "API Keys" 部分
3. 创建新的 API Key 或使用现有 Key

## 依赖要求

- Python >= 3.9
- requests >= 2.28.0

## 参考文档

- [Cursor Cloud Agents API 文档](https://cursor.com/cn/docs/cloud-agent/api/endpoints)

