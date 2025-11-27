# ShowDoc 自动化工具集

从 ShowDoc 自动获取 API 文档数据，并生成 Android 代码的 Python 工具集。

## 项目结构

```
fengli/
├── core/                   # 核心模块：ShowDoc 客户端、验证码识别
├── android_codegen/        # Android 代码生成工具（Entity、Repository、Retrofit）
├── api_docs/              # API 文档示例和预研文档
├── mcp_showdoc_android/   # MCP 服务器实现
└── pyproject.toml         # 项目配置
```

## 核心功能

### 1. ShowDoc 数据获取 (`core/`)

- 自动登录（支持密码或 Cookie 认证）
- 验证码识别（基于 PaddleOCR）
- 结构化数据解析（分类、页面、API 定义）
- 支持按节点筛选数据

### 2. Android 代码生成 (`android_codegen/`)

- Entity 实体类生成
- Repository 数据仓库生成
- Retrofit 接口生成
- OkHttp 配置生成

### 3. MCP 服务器 (`mcp_showdoc_android/`)

- 提供 MCP 协议接口
- 支持通过 MCP 调用代码生成功能

## 快速开始

### 安装依赖

```bash
# 安装核心依赖
pip install -r core/requirements.txt

# 或安装完整项目（包括 MCP 服务器）
pip install -e .
```

### 基本使用

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

### 测试

```bash
# 运行核心模块测试
cd core
python test.py

# 或从项目根目录运行
python -m core.test
```

## 模块说明

- **core/**: ShowDoc 客户端核心实现，详见 [core/README.md](core/README.md)
- **android_codegen/**: Android 代码生成工具，详见 [android_codegen/README.md](android_codegen/README.md)
- **mcp_showdoc_android/**: MCP 服务器，详见 [mcp_showdoc_android/README.md](mcp_showdoc_android/README.md)
- **api_docs/**: API 文档示例，详见 [api_docs/README.md](api_docs/README.md)

## 依赖要求

- Python >= 3.9
- 核心依赖：requests, opencv-python, numpy, paddlepaddle, paddleocr

## 开发规范

本项目遵循以下规范：

- 使用简体中文进行注释和文档
- 优先使用现代 Python 特性（类型注解、dataclass 等）
- 模块化设计，保持单一职责
- 详细的异常处理和错误提示

## 许可证

本项目为内部工具，仅供团队使用。

