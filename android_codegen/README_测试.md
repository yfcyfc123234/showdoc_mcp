# Android 代码生成器测试说明

## 测试文件

统一使用 `android_codegen/test.py` 进行测试。

## 快速开始

### 方式1: 在 android_codegen 目录内运行

```bash
cd android_codegen
python test.py
```

### 方式2: 从项目根目录运行

```bash
python -m android_codegen.test
```

## 配置参数

打开 `android_codegen/test.py`，修改以下配置：

```python
# ShowDoc URL（复用 core 模块的配置）
BASE_URL = "https://doc.cqfengli.com/web/#/90"

# Cookie（用于认证，复用 core 模块的配置）
COOKIE = "think_language=zh-CN; PHPSESSID=xxx"

# 节点名称（None=全部，或指定节点名称如 "订单"）
NODE_NAME = None

# Android 代码生成配置
BASE_PACKAGE = "com.example.api"  # Android 包名
OUTPUT_DIR = "android_output"     # 默认输出目录

# 输出目录配置
# None: 使用默认目录（android_output）
# 字符串: 导出到指定目录，支持 {item_id} 占位符
OUTPUT_DIR_CONFIG = None  # 例如: "output/android_{item_id}"

# 自动生成控制
# True: 自动生成代码（如果 OUTPUT_DIR_CONFIG 为 None，使用默认目录）
# False: 交互式询问是否生成（仅在交互式环境下）
AUTO_GENERATE = True

# 是否显示详细的 API 信息
SHOW_DETAILS = True
```

## 输出目录配置详解

### 配置选项

在 `android_codegen/test.py` 中有两个参数控制生成行为：

```python
# 输出目录配置
# None: 使用默认目录（android_output）
# 字符串: 导出到指定目录，支持 {item_id} 占位符
OUTPUT_DIR_CONFIG = None  # 例如: "output/android_{item_id}"

# 自动生成控制
# True: 自动生成代码（如果 OUTPUT_DIR_CONFIG 为 None，使用默认目录）
# False: 交互式询问是否生成（仅在交互式环境下）
AUTO_GENERATE = True
```

### 生成行为说明

| AUTO_GENERATE | OUTPUT_DIR_CONFIG | 行为 |
|--------------|-------------------|------|
| `False` | `None` | 交互式询问是否生成，使用默认目录 |
| `False` | `"路径"` | 交互式询问是否生成，使用指定目录 |
| `True` | `None` | 自动生成到默认目录（`android_output`） |
| `True` | `"路径"` | 自动生成到指定目录 |

### 配置示例

#### 1. 交互式生成（默认）

```python
OUTPUT_DIR_CONFIG = None
AUTO_GENERATE = False
```

运行时会询问是否生成。如果非交互式环境（如脚本自动运行），会跳过生成。

#### 2. 自动生成到默认路径

```python
OUTPUT_DIR_CONFIG = None
AUTO_GENERATE = True
```

自动生成到默认目录 `android_output`，不会询问。

#### 3. 自动生成到指定路径

```python
OUTPUT_DIR_CONFIG = "output/android_code"
AUTO_GENERATE = True
```

会直接生成到指定目录，不会询问。

#### 4. 使用项目ID占位符

```python
OUTPUT_DIR_CONFIG = "output/android_{item_id}"
AUTO_GENERATE = True
```

如果项目ID是 90，会生成到 `output/android_90`。`{item_id}` 会自动替换为实际的项目ID。

#### 5. 按项目ID分类存储

```python
OUTPUT_DIR_CONFIG = "generated/{item_id}/android"
AUTO_GENERATE = True
```

会生成到 `generated/90/android`，目录会自动创建。

#### 6. 带时间戳的路径

```python
import datetime
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR_CONFIG = f"output/android_{timestamp}"
AUTO_GENERATE = True
```

每次运行都会生成到带时间戳的目录，便于保存历史版本。

### 路径占位符

如果路径中包含 `{item_id}`，会自动替换为实际的项目ID：

```python
OUTPUT_DIR_CONFIG = "generated/{item_id}/android"
# 如果项目ID是 90，实际输出目录为: generated/90/android
```

### 目录自动创建

如果指定的目录不存在，程序会自动创建：

```python
OUTPUT_DIR_CONFIG = "output/subfolder/android_code"
# 如果 output/subfolder/ 不存在，会自动创建
```

### 使用场景

1. **开发环境**: 使用默认目录
   ```python
   OUTPUT_DIR_CONFIG = None  # 或 "android_output"
   ```

2. **生产环境**: 使用专门的输出目录
   ```python
   OUTPUT_DIR_CONFIG = "generated/android_code"
   ```

3. **多项目**: 按项目ID分类存储
   ```python
   OUTPUT_DIR_CONFIG = "generated/{item_id}/android"
   ```

4. **带时间戳**: 保存历史版本
   ```python
   import datetime
   timestamp = datetime.datetime.now().strftime("%Y%m%d")
   OUTPUT_DIR_CONFIG = f"generated/android_{timestamp}"
   ```

### 注意事项

- 路径分隔符：
  - Windows: `"output\\android_code"` 或 `"output/android_code"`（两种都可以）
  - Linux/Mac: `"output/android_code"`

- 目录会自动创建

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
# 显示详细 API 信息（默认）
SHOW_DETAILS = True

# 只显示统计信息，不显示详细列表
SHOW_DETAILS = False
```

## 生成的文件结构

生成完成后，输出目录结构如下：

```
android_output/
├── services/
│   └── ApiService.kt           # Retrofit Service 接口
├── entities/
│   ├── OrderResponse.kt        # 订单响应实体类
│   ├── UserResponse.kt         # 用户响应实体类
│   └── ...
└── config/
    ├── OkHttpConfig.kt         # OkHttp 配置
    └── dependencies.gradle.kts # Gradle 依赖配置
```

## 集成到 Android 项目

### 1. 添加依赖

将生成的 `dependencies.gradle.kts` 中的依赖添加到你的 `build.gradle.kts`:

```kotlin
dependencies {
    // Retrofit
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    
    // OkHttp
    implementation("com.squareup.okhttp3:okhttp:4.11.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.11.0")
    
    // Gson
    implementation("com.google.code.gson:gson:2.10.1")
}
```

### 2. 复制生成的代码

将生成的文件复制到你的 Android 项目中：
- `services/ApiService.kt` → `app/src/main/java/com/example/api/services/`
- `entities/*.kt` → `app/src/main/java/com/example/api/entities/`
- `config/OkHttpConfig.kt` → `app/src/main/java/com/example/api/config/`

### 3. 配置 API 基础 URL

编辑 `OkHttpConfig.kt`，修改 `BASE_URL` 为实际的 API 服务器地址：

```kotlin
private const val BASE_URL = "https://your-api-server.com"
```

### 4. 使用生成的代码

```kotlin
// 在 Repository 或 ViewModel 中使用
class OrderRepository {
    private val apiService = OkHttpConfig.createApiService()
    
    suspend fun getOrders(): Result<OrderListResponse> {
        return try {
            val response = apiService.getOrders(page = 1, size = 20)
            if (response.isSuccessful) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("请求失败"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
```

## 常见问题

### 1. 认证失败

**错误**: `ShowDocAuthError: 认证失败`

**解决**: 检查 Cookie 是否有效，重新登录 ShowDoc 获取新 Cookie。

### 2. 节点不存在

**错误**: `ShowDocNotFoundError: 未找到指定节点`

**解决**: 
- 检查节点名称是否正确（区分大小写）
- 先用 `NODE_NAME = None` 获取所有节点，查看正确的节点名称

### 3. 模块导入错误

**错误**: `ModuleNotFoundError: No module named 'core'` 或 `ModuleNotFoundError: No module named 'android_codegen'`

**解决**: 
- 确保在项目根目录或 android_codegen 目录下运行
- 使用 `python -m android_codegen.test` 的方式运行
- 确保已安装所有依赖（参考根目录 `requirements.txt`）

### 4. 生成的代码需要手动调整

**说明**: 当前版本的类型推断较为简单，可能需要：
- 手动调整实体类的类型定义
- 根据实际 API 响应结构修改实体类属性
- 添加自定义的请求/响应包装类型

## 获取 Cookie

1. 在浏览器中登录 ShowDoc
2. 打开开发者工具（F12）
3. 切换到 Network（网络）标签
4. 刷新页面
5. 点击任意请求
6. 在 Request Headers 中找到 Cookie
7. 复制 Cookie 的值

## 与 core 模块的关系

本测试脚本依赖 `core` 模块来获取 ShowDoc 数据：

1. 使用 `core.ShowDocClient` 获取 API 数据
2. 将获取的 `ApiTree` 对象传递给 `AndroidCodeGenerator` 生成代码
3. 复用了 `core/test.py` 的配置参数（BASE_URL, COOKIE 等）

因此，如果 `core/test.py` 能正常运行，本测试脚本也应该能正常运行。

