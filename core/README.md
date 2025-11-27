# ShowDoc 数据获取核心模块

该模块提供了从 ShowDoc 自动获取接口文档数据的功能。

## 安装依赖

```bash
# 推荐：从项目根目录安装
python -m pip install -r ../requirements.txt

# 或在 core 目录内安装（兼容旧流程）
python -m pip install -r requirements.txt
```

### 验证码识别

项目使用 **ddddocr** 进行验证码识别，这是一个基于深度学习的通用验证码识别库：
- 识别准确率高
- 支持多种验证码类型（数字、字母、混合等）
- 无需额外安装 OCR 程序，纯 Python 实现
- 项目地址：https://github.com/sml2h3/ddddocr

安装依赖后即可使用，无需额外配置。

## 使用方法

### 基本使用

```python
from core import ShowDocClient

# 初始化客户端（方式1：使用密码自动登录，默认密码 123456）
base_url = "https://doc.cqfengli.com/web/#/90/"
client = ShowDocClient(base_url, password="123456")

# 或方式2：使用 Cookie
cookie = "think_language=zh-CN; PHPSESSID=tg7ja3au64div38p58abmomtt6"
client = ShowDocClient(base_url, cookie=cookie)

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

#### `__init__(base_url: str, cookie: Optional[str] = None, password: Optional[str] = "123456")`

初始化客户端。

- `base_url`: ShowDoc 文档页面 URL，支持多种格式：
  - 标准格式：`"https://doc.cqfengli.com/web/#/90/"`
  - 登录页面格式：`"https://doc.cqfengli.com/web/#/item/password/88?page_id=4091"`
- `cookie`: 认证 Cookie（可选），例如 `"think_language=zh-CN; PHPSESSID=xxx"`
- `password`: 项目访问密码（可选，默认: "123456"），如果提供且 cookie 为空，将自动进行验证码登录

**Cookie 自动管理**：
- 登录成功后的 Cookie 会自动保存到本地文件 `.showdoc_cookies.json`
- 下次运行时，如果 Cookie 有效且未过期，会自动复用，无需重新登录
- Cookie 优先级：传入的 Cookie > 保存的 Cookie > 密码登录
- Cookie 默认过期时间：24 小时

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
    client = ShowDocClient(base_url, password="123456")
    api_tree = client.get_all_apis("订单")
except ShowDocNotFoundError as e:
    print(f"节点不存在: {e}")
except ShowDocAuthError as e:
    print(f"认证失败: {e}")
except Exception as e:
    print(f"其他错误: {e}")
```

## 验证码调试

- 使用 ddddocr 进行验证码识别，支持多种验证码类型
- 登录失败（验证码错误或识别异常）时，会自动重试并将失败的验证码图片保存到 `captcha_debug/` 目录，便于人工排查
- 每次运行程序时会自动清理旧的调试目录，只保留当前会话的调试信息
- 可通过环境变量修改保存目录：
  ```bash
  # PowerShell
  $env:SHOWDOC_CAPTCHA_DEBUG_DIR="D:\tmp\captcha_debug"
  ```
- 如果验证码持续无法识别，可在 `core/test.py` 中直接配置 COOKIE，或手动输入验证码

