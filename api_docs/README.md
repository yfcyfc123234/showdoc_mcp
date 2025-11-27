# ShowDoc MCP 服务接口文档

## 项目说明

本项目旨在开发一个适用于 Cursor 的 ShowDoc MCP 服务，使用 Python 实现。

### 项目背景

当前存在以下痛点：
- 服务器将接口文档发布在网页中
- 客户端开发者需要手动查看 API 地址定义、请求参数、返回格式等信息
- 步骤重复繁琐，严重影响开发效率

### 解决方案

通过为 MCP 服务提供 ShowDoc 服务器接口地址（URL）和用户认证信息（Cookie 或密码），实现：
- 按指定层级自动获取所有接口数据
- 将数据封装为标准化格式（类似 Android 实体类及 Retrofit Service 配置）
- 支持自动验证码登录（当提供密码时）

## 接口调用流程

### 步骤 1: 访问主页面

**接口地址**: `https://doc.cqfengli.com/web/`

**说明**: 这是访问 ShowDoc 的初始步骤，通过 GET 请求获取主页面 HTML，页面中包含服务器配置信息（如 API 基础路径、静态资源路径等），为后续 API 调用做准备。

**详细请求示例**: [接口示例 1](api_example_01.txt)

---

### 步骤 2: 获取文档目录结构

**接口地址**: `https://doc.cqfengli.com/server/index.php?s=/api/item/info`

**说明**: 通过 POST 请求获取指定文档项目的完整目录树结构，包括所有分类（category）和页面（page）的层级关系、ID 等信息。此步骤用于了解文档的整体结构，便于后续遍历所有页面。

**详细请求示例**: [接口示例 2](api_example_02.txt)

---

### 步骤 3: 获取 AI 知识库配置（可选）

**接口地址**: `https://doc.cqfengli.com/server/index.php?s=/api/item/getAiKnowledgeBaseConfig`

**说明**: 获取文档项目的 AI 知识库相关配置信息，可能与 ShowDoc 的 AI 功能相关。此步骤为可选步骤，不影响接口文档的获取。

**详细请求示例**: [接口示例 3](api_example_03.txt)

---

### 步骤 4: 获取页面详细信息

**接口地址**: `https://doc.cqfengli.com/server/index.php?s=/api/page/info`

**说明**: 根据页面 ID（page_id）获取指定页面的完整详细信息，包括 API 接口定义、请求方法、请求参数、请求头、响应格式等。这是获取接口文档的核心步骤，返回的 `page_content` 字段包含完整的接口定义（需进行 HTML 实体解码和 JSON 解析）。

**详细请求示例**: [接口示例 4](api_example_04.txt)

---


## 数据处理注意事项

### HTML 实体编码处理

在步骤 4 返回的数据中，`page_content` 字段是一个经过 HTML 实体编码的 JSON 字符串。`&quot;` 是 HTML 实体编码，代表双引号 `"`。

**编码原因**: 由于 `page_content` 字段的值本身就是一个嵌套的 JSON 字符串，为了在 JSON 响应中避免双引号冲突，ShowDoc 对内部 JSON 进行了 HTML 实体转义。

**解码步骤**:
1. 使用 HTML 实体解码，将 `&quot;` 转换为 `"`
2. 将解码后的字符串解析为 JSON 对象

示例（Python）：
import json
import html

# 假设从接口获取的原始数据
raw_data = {
    "error_code": 0,
    "data": {
        "page_content": "{&quot;page_title&quot;:&quot;\u83b7\u53d6\u62cd\u7167\u6559\u7a0b&quot;,...}"
    }
}

# 1. 获取 page_content 字符串
encoded_content = raw_data["data"]["page_content"]

# 2. HTML实体解码
decoded_content = html.unescape(encoded_content)

# 3. 解析为 JSON 对象
page_content = json.loads(decoded_content)

print(page_content["page_title"])  # 输出：获取拍照教程

---

## 自动登录流程

当项目设置了访问密码时，可以使用密码自动登录，无需手动获取 Cookie。

### 认证方式

支持两种认证方式（二选一）：
1. **Cookie 认证**：手动在浏览器中登录后，复制 Cookie 字符串（推荐用于已登录场景）
2. **密码认证**：提供项目访问密码，系统将自动进行验证码识别和登录

### 自动密码登录流程

如果提供了 `password` 参数且未提供 `cookie`，系统将自动执行以下步骤：

1. **创建验证码会话**
   - 接口：`POST /api/common/createCaptcha`
   - 返回：`captcha_id`（验证码会话 ID）

2. **获取验证码图片**
   - 接口：`GET /api/common/showCaptcha?captcha_id={captcha_id}&{timestamp}`
   - 返回：验证码图片（PNG/JPEG 格式）

3. **识别验证码**
   - 使用 ddddocr 进行验证码识别
   - 支持自动重试（默认最多 5 次）

4. **提交密码和验证码**
   - 接口：`POST /api/item/pwd`
   - 参数：`item_id`, `password`, `captcha`, `captcha_id`
   - 成功：服务器返回 `error_code=0` 并设置 Cookie（`PHPSESSID` 等）

5. **使用 Cookie 继续后续请求**
   - 登录成功后，自动从 session 中提取 Cookie
   - 后续所有 API 请求都会自动携带该 Cookie

### 错误处理

- **验证码识别失败**：自动刷新验证码并重试（最多 5 次）
- **验证码错误**（error_code=10206）：自动刷新验证码并重试
- **密码错误**（error_code=10303 等）：立即抛出 `ShowDocAuthError`，不重试
- **达到最大重试次数**：抛出 `ShowDocAuthError`，提示人工介入

### 依赖要求

自动登录功能需要以下 Python 包：
- `opencv-python>=4.8.0`：图像处理
- `numpy>=1.24.0`：数组操作
- `ddddocr>=1.4.0`：验证码识别

ddddocr 是纯 Python 实现，无需额外安装 OCR 程序，安装依赖后即可使用。

### 使用示例

```python
from core import ShowDocClient

# 方式 1：使用密码自动登录（推荐，默认密码 123456）
client = ShowDocClient(
    base_url="https://doc.cqfengli.com/web/#/90/",
    password="123456"  # 默认密码，可省略
)

# 方式 2：使用 Cookie（传统方式）
client = ShowDocClient(
    base_url="https://doc.cqfengli.com/web/#/90/",
    cookie="PHPSESSID=xxx; think_language=zh-CN"
)

# 后续使用方式相同
api_tree = client.get_all_apis(node_name="订单")
```

### 注意事项

- 验证码识别成功率取决于验证码复杂度，简单验证码（如纯数字+字母，无严重扭曲）识别率较高
- 如果验证码识别持续失败，建议使用 Cookie 方式作为备选方案
- 密码登录成功后，Cookie 会保存在 session 中，可以复用进行后续请求
