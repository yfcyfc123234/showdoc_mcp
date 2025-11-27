# ShowDoc 数据获取核心模块

该模块提供了从 ShowDoc 自动获取接口文档数据的功能。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本使用

```python
from core import ShowDocClient

# 初始化客户端
base_url = "https://doc.cqfengli.com/web/#/90/"
cookie = "think_language=zh-CN; PHPSESSID=tg7ja3au64div38p58abmomtt6"

client = ShowDocClient(base_url, cookie)

# 获取所有接口数据
api_tree = client.get_all_apis()

# 或者只获取指定节点的数据
api_tree = client.get_all_apis(node_name="订单")

# 转换为字典格式
data = api_tree.to_dict()

# 或者直接访问结构化的数据
for category in api_tree.categories:
    print(f"分类: {category.cat_name}")
    for page in category.pages:
        if page.api_info:
            print(f"  - {page.page_title}: {page.api_info.method} {page.api_info.url}")
```

### 获取指定节点的数据

```python
# 获取所有节点
api_tree = client.get_all_apis()  # 或 client.get_all_apis("全部") 或 client.get_all_apis("all")

# 获取指定节点（如"订单"）
api_tree = client.get_all_apis("订单")
```

### 数据结构

返回的 `ApiTree` 对象包含：

- `item_info`: 项目信息（ItemInfo）
- `categories`: 分类列表（List[Category]）
  - 每个 `Category` 包含：
    - `cat_id`, `cat_name`, `level`, `parent_cat_id`
    - `pages`: 页面列表（List[Page]）
    - `children`: 子分类列表（List[Category]）
  - 每个 `Page` 包含：
    - `page_id`, `page_title`
    - `api_info`: API 定义（ApiDefinition，如果不是 API 页面则为 None）
      - `method`: HTTP 方法（GET, POST 等）
      - `url`: 接口 URL
      - `request`: 请求参数信息
      - `response`: 响应信息

## API 方法

### ShowDocClient

#### `__init__(base_url: str, cookie: str)`

初始化客户端。

- `base_url`: ShowDoc 文档页面 URL，例如 `"https://doc.cqfengli.com/web/#/90/"`
- `cookie`: 认证 Cookie，例如 `"think_language=zh-CN; PHPSESSID=xxx"`

#### `get_all_apis(node_name: Optional[str] = None) -> ApiTree`

获取所有接口数据（主入口方法）。

- `node_name`: 节点名称（分类名称）
  - `None` / `"全部"` / `"all"`: 获取所有节点
  - 具体名称（如 `"订单"`）: 只获取该节点及其子节点的数据
- 返回: `ApiTree` 对象

#### `fetch_homepage() -> Dict[str, Any]`

访问主页面获取配置信息。

#### `fetch_item_info(item_id: Optional[str] = None) -> Dict[str, Any]`

获取文档目录结构。

#### `fetch_page_info(page_id: str) -> Dict[str, Any]`

获取单个页面的详细信息。

## 异常处理

模块定义了以下自定义异常：

- `ShowDocError`: 基础异常类
- `ShowDocAuthError`: 认证错误（Cookie 无效等）
- `ShowDocNotFoundError`: 资源未找到（节点、页面不存在等）
- `ShowDocParseError`: 数据解析错误
- `ShowDocNetworkError`: 网络请求错误

使用示例：

```python
from core import ShowDocClient, ShowDocNotFoundError, ShowDocAuthError

try:
    client = ShowDocClient(base_url, cookie)
    api_tree = client.get_all_apis("订单")
except ShowDocNotFoundError as e:
    print(f"节点不存在: {e}")
except ShowDocAuthError as e:
    print(f"认证失败: {e}")
except Exception as e:
    print(f"其他错误: {e}")
```

