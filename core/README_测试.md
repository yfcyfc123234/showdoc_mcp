# ShowDoc 核心模块测试说明

## 测试文件

统一使用 `core/test.py` 进行测试。

## 快速开始

### 方式1: 在 core 目录内运行

```bash
cd core
python test.py
```

### 方式2: 从项目根目录运行

```bash
python -m core.test
```

## 配置参数

打开 `core/test.py`，修改以下配置：

```python
# ShowDoc URL
BASE_URL = "https://doc.cqfengli.com/web/#/90"

# Cookie（用于认证，可选，如果提供 password 则可不提供）
COOKIE = None  # 可选，如果提供则使用 Cookie 认证

# 节点名称（None=全部，或指定节点名称如 "订单"）
NODE_NAME = None

# 导出路径配置
# None: 使用默认文件名（showdoc_export_{item_id}.json）
# 字符串: 导出到指定路径，支持 {item_id} 占位符
EXPORT_PATH = None  # 例如: "output/showdoc_{item_id}.json"

# 自动导出控制
# True: 自动导出（如果 EXPORT_PATH 为 None，使用默认文件名）
# False: 交互式询问是否导出（仅在交互式环境下）
AUTO_EXPORT = False

# 是否显示详细的分类结构
SHOW_DETAILS = True
```

## 导出路径配置详解

### 配置选项

在 `core/test.py` 中有两个参数控制导出行为：

```python
# 导出文件路径配置
# None: 使用默认文件名（showdoc_export_{item_id}.json）
# 字符串: 导出到指定路径，支持 {item_id} 占位符
EXPORT_PATH = None  # 例如: "output/showdoc_{item_id}.json"

# 自动导出控制
# True: 自动导出（如果 EXPORT_PATH 为 None，使用默认文件名）
# False: 交互式询问是否导出（仅在交互式环境下）
AUTO_EXPORT = False
```

### 导出行为说明

| AUTO_EXPORT | EXPORT_PATH | 行为 |
|------------|-------------|------|
| `False` | `None` | 交互式询问是否导出，使用默认文件名 |
| `False` | `"路径"` | 交互式询问是否导出，使用指定路径 |
| `True` | `None` | 自动导出到默认文件名（`showdoc_export_{item_id}.json`） |
| `True` | `"路径"` | 自动导出到指定路径 |

### 配置示例

#### 1. 交互式导出（默认）

```python
EXPORT_PATH = None
AUTO_EXPORT = False
```

运行时会询问是否导出。如果非交互式环境（如脚本自动运行），会跳过导出。

### 1.1 自动导出到默认路径

```python
EXPORT_PATH = None
AUTO_EXPORT = True
```

自动导出到默认文件名 `showdoc_export_{item_id}.json`，不会询问。

#### 2. 自动导出到固定路径

```python
EXPORT_PATH = "output/showdoc_data.json"
```

会直接导出到指定路径，不会询问。

#### 3. 使用项目ID占位符

```python
EXPORT_PATH = "output/showdoc_{item_id}.json"
```

如果项目ID是 90，会导出到 `output/showdoc_90.json`。`{item_id}` 会自动替换为实际的项目ID。

#### 4. 按项目ID分类存储

```python
EXPORT_PATH = "data/{item_id}/export.json"
```

会导出到 `data/90/export.json`，目录会自动创建。

#### 5. 带时间戳的路径

```python
import datetime
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
EXPORT_PATH = f"output/showdoc_{timestamp}.json"
```

每次运行都会生成带时间戳的文件名，便于保存历史版本。

### 路径占位符

如果路径中包含 `{item_id}`，会自动替换为实际的项目ID：

```python
EXPORT_PATH = "data/{item_id}/export.json"
# 如果项目ID是 90，实际导出路径为: data/90/export.json
```

### 目录自动创建

如果指定的路径中的目录不存在，程序会自动创建：

```python
EXPORT_PATH = "output/subfolder/data.json"
# 如果 output/subfolder/ 不存在，会自动创建
```

### 使用场景

1. **开发环境**: 使用默认路径或项目根目录
   ```python
   EXPORT_PATH = None  # 或 "showdoc_export_{item_id}.json"
   ```

2. **生产环境**: 使用专门的输出目录
   ```python
   EXPORT_PATH = "data/exports/showdoc_{item_id}.json"
   ```

3. **多项目**: 按项目ID分类存储
   ```python
   EXPORT_PATH = "exports/{item_id}/data.json"
   ```

4. **带时间戳**: 保存历史版本
   ```python
   import datetime
   timestamp = datetime.datetime.now().strftime("%Y%m%d")
   EXPORT_PATH = f"exports/showdoc_{timestamp}.json"
   ```

### 注意事项

- 路径分隔符：
  - Windows: `"output\\data.json"` 或 `"output/data.json"`（两种都可以）
  - Linux/Mac: `"output/data.json"`

- 路径中的目录会自动创建，但文件需要是 `.json` 扩展名

## 测试节点筛选

修改 `NODE_NAME` 参数：

```python
# 获取所有节点
NODE_NAME = None  # 或 NODE_NAME = "全部"

# 获取指定节点
NODE_NAME = "订单"
```

## 详细输出控制

```python
# 显示详细分类结构（默认）
SHOW_DETAILS = True

# 只显示统计信息，不显示详细结构
SHOW_DETAILS = False
```

## 常见问题

### 1. 认证失败

**错误**: `ShowDocAuthError: 认证失败`

**解决**: 
- 如果使用密码登录：验证码识别失败或密码错误，会自动重试（最多 5 次）
- 如果使用 Cookie：检查 Cookie 是否有效，重新登录 ShowDoc 获取新 Cookie
- 如果使用保存的 Cookie：可能已过期，删除 `.showdoc_cookies.json` 后重新登录

### 2. 节点不存在

**错误**: `ShowDocNotFoundError: 未找到指定节点`

**解决**: 
- 检查节点名称是否正确（区分大小写）
- 先用 `NODE_NAME = None` 获取所有节点，查看正确的节点名称

### 3. 模块导入错误

**错误**: `ModuleNotFoundError: No module named 'core'`

**解决**: 
- 确保在项目根目录或 core 目录下运行
- 使用 `python -m core.test` 的方式运行

## Cookie 管理

### 方式1：自动保存和复用（推荐）

使用密码登录时，Cookie 会自动保存到 `.showdoc_cookies.json`，下次运行时自动复用：

```python
# 第一次运行 - 使用密码登录
client = ShowDocClient(BASE_URL, password="123456")
# Cookie 会自动保存

# 第二次运行 - 自动使用保存的 Cookie，无需再次登录
client = ShowDocClient(BASE_URL, password="123456")
# 会自动加载保存的 Cookie
```

### 方式2：手动获取 Cookie

如果需要手动获取 Cookie：

1. 在浏览器中登录 ShowDoc
2. 打开开发者工具（F12）
3. 切换到 Network（网络）标签
4. 刷新页面
5. 点击任意请求
6. 在 Request Headers 中找到 Cookie
7. 复制 Cookie 的值

