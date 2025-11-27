# Android 代码生成器

将 core 模块从 ShowDoc 获取的 API 数据自动转换为 Android 项目可用的代码。

## 功能特性

- ✅ **Retrofit2 Service 接口生成** - 自动生成 Retrofit 接口定义
- ✅ **Android 实体类生成** - 自动生成 Kotlin Data Class
- ✅ **OkHttp 配置生成** - 自动生成 OkHttp 和 Retrofit 配置代码
- ✅ **依赖配置生成** - 生成所需的 Gradle 依赖配置

## 目录结构

```
android_codegen/
├── __init__.py              # 模块初始化
├── generator.py             # 主生成器类
├── retrofit_generator.py    # Retrofit Service 生成器
├── entity_generator.py      # 实体类生成器
├── okhttp_config.py         # OkHttp 配置生成器
├── test.py                  # 测试脚本（推荐使用）
├── README.md                # 使用文档
└── README_测试.md           # 测试说明文档
```

## 快速开始

### 使用测试脚本（推荐）

最简单的方式是使用测试脚本：

```bash
# 方式1: 在 android_codegen 目录内运行
cd android_codegen
python test.py

# 方式2: 从项目根目录运行
python -m android_codegen.test
```

测试脚本会自动从 ShowDoc 获取数据并生成 Android 代码。详细说明请参考 [README_测试.md](README_测试.md)。

### 编程方式使用

#### 基本使用

```python
from core import ShowDocClient
from android_codegen import AndroidCodeGenerator

# 1. 从 ShowDoc 获取 API 数据
client = ShowDocClient(
    base_url="https://doc.cqfengli.com/web/#/90/",
    cookie="think_language=zh-CN; PHPSESSID=xxx"
)
api_tree = client.get_all_apis(node_name="订单")

# 2. 生成 Android 代码
generator = AndroidCodeGenerator(
    base_package="com.example.api",
    output_dir="android_output"
)

# 3. 生成代码文件
generated_files = generator.generate(api_tree)

print("生成的文件:")
print(f"  Service: {generated_files['services']}")
print(f"  Entities: {generated_files['entities']}")
print(f"  Config: {generated_files['config']}")
```

### 生成的代码结构

生成的代码将保存在指定的输出目录中：

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

## 生成的代码示例

### Retrofit Service 接口

```kotlin
package com.example.api.services

import retrofit2.http.*
import retrofit2.Response
import com.example.api.entities.*

interface ApiService {
    /**
     * 获取订单列表
     * API: GET /api/orders
     */
    @GET("/api/orders")
    suspend fun getOrders(
        @Query("page") page: Int?,
        @Query("size") size: Int?
    ): Response<OrderListResponse>
}
```

### Android 实体类

```kotlin
package com.example.api.entities

import android.os.Parcelable
import kotlinx.parcelize.Parcelize

@Parcelize
data class OrderResponse(
    var order_id: String,
    var user_id: String,
    var amount: Double,
    var status: Int?
) : Parcelable
```

**注意**：
- 所有实体类都使用 `@Parcelize` 注解和 `Parcelable` 接口，方便在 Activity/Fragment 间传递
- 字段名保持与服务器一致，不使用 `@SerializedName` 注解
- 需要在 `build.gradle.kts` 中添加 `id("kotlin-parcelize")` 插件

### OkHttp 配置

```kotlin
package com.example.api.config

object OkHttpConfig {
    private const val BASE_URL = "https://api.example.com"
    
    fun createApiService(): ApiService {
        return Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(createOkHttpClient())
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }
}
```

## 配置选项

### AndroidCodeGenerator 参数

- `base_package` (str): Android 项目的基础包名，默认为 `"com.example.api"`
- `output_dir` (str): 输出目录，默认为 `"android_output"`

### 筛选分类

```python
# 生成特定分类的代码
generated_files = generator.generate(
    api_tree,
    category_filter="订单"  # 只生成"订单"分类下的 API
)
```

## 集成到 Android 项目

### 1. 添加依赖和插件

在 `build.gradle.kts` 的 `plugins` 块中添加 Parcelize 插件：

```kotlin
plugins {
    // ... 其他插件
    id("kotlin-parcelize")
}
```

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

### 3. 使用生成的代码

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

## 注意事项

1. **类型推断限制**: 当前版本的类型推断较为简单，可能需要手动调整生成的实体类
2. **API 路径参数**: 路径参数（如 `/api/users/{id}`）会自动转换为 `@Path` 注解
3. **请求体类型**: 复杂请求体可能需要手动定义对应的 Data Class
4. **响应包装**: 所有响应都使用 `ResponseData<T>` 统一包装格式（`{code, msg, data, hasNext}`）
5. **Parcelize 插件**: 生成的实体类都使用 `@Parcelize` 和 `Parcelable`，需要在 `build.gradle.kts` 中添加 `id("kotlin-parcelize")` 插件
6. **字段命名**: 实体类字段名保持与服务器一致，不进行转换，也不使用 `@SerializedName` 注解

## 为 MCP 化做准备

本模块设计时已考虑 MCP（Model Context Protocol）集成：

- 模块化设计，易于作为 MCP 工具暴露
- 输入输出清晰，符合 MCP 工具规范
- 可扩展性强，方便添加新的代码生成功能

## 后续改进计划

- [ ] 支持自定义代码模板
- [ ] 支持多种 JSON 解析库（Gson、Moshi、Kotlinx Serialization）
- [ ] 支持响应包装类型自动识别
- [ ] 支持请求拦截器自动生成
- [ ] 支持多环境配置（开发、测试、生产）
- [ ] 生成单元测试代码模板

