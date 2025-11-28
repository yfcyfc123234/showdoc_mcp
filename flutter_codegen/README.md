# Flutter 代码生成器

将 core 模块从 ShowDoc 获取的 API 数据自动转换为 Flutter 项目可用的代码。

## 功能特性

- ✅ **Dio Service 接口生成** - 自动生成 Dio 接口定义
- ✅ **Dart 实体类生成** - 自动生成 Dart 类（使用 json_serializable）
- ✅ **Repository 层生成** - 自动生成 Repository 类
- ✅ **Dio 配置生成** - 自动生成 Dio 配置代码
- ✅ **依赖配置生成** - 生成所需的 pubspec.yaml 依赖配置

## 技术选型

- **网络库**: Dio（Flutter 最流行的网络库）
- **JSON 序列化**: json_serializable（官方推荐，类型安全）
- **架构**: Repository 模式（类似 Android）

## 目录结构

```
flutter_codegen/
├── __init__.py              # 模块初始化
├── generator.py             # 主生成器类
├── dio_service_generator.py # Dio Service 生成器
├── entity_generator.py      # 实体类生成器
├── repository_generator.py  # Repository 生成器
├── dio_config.py            # Dio 配置生成器
├── test.py                  # 测试脚本（推荐使用）
└── README.md                # 使用文档
```

## 快速开始

### 使用测试脚本（推荐）

最简单的方式是使用测试脚本：

```bash
# 方式1: 在 flutter_codegen 目录内运行
cd flutter_codegen
python test.py

# 方式2: 从项目根目录运行
python -m flutter_codegen.test
```

测试脚本会自动从 ShowDoc 获取数据并生成 Flutter 代码。

### 编程方式使用

#### 基本使用

```python
from core import ShowDocClient
from flutter_codegen import FlutterCodeGenerator

# 1. 从 ShowDoc 获取 API 数据
# 方式1：使用密码自动登录（推荐，Cookie 会自动保存）
client = ShowDocClient(
    base_url="https://doc.cqfengli.com/web/#/90/",
    password="123456"  # 默认密码，可省略
)

# 方式2：使用 Cookie（如果已有保存的 Cookie，会自动复用）
client = ShowDocClient(
    base_url="https://doc.cqfengli.com/web/#/90/",
    cookie="think_language=zh-CN; PHPSESSID=xxx"
)

api_tree = client.get_all_apis(node_name="订单")

# 2. 生成 Flutter 代码
generator = FlutterCodeGenerator(
    base_package="com.example.api",
    output_dir="flutter_output"
)

# 3. 生成代码文件
generated_files = generator.generate(api_tree)

print("生成的文件:")
print(f"  Service: {generated_files['services']}")
print(f"  Models: {generated_files['models']}")
print(f"  Repositories: {generated_files['repositories']}")
print(f"  Config: {generated_files['config']}")
```

### 生成的代码结构

生成的代码将保存在指定的输出目录中：

```
flutter_output/
├── services/
│   └── api_service.dart           # Dio Service 接口
├── models/
│   ├── response_data.dart        # 响应数据基类
│   └── [category]/
│       ├── request/
│       │   └── [entity].dart     # 请求实体类
│       └── response/
│           └── [entity].dart     # 响应实体类
├── repositories/
│   └── api_repository.dart       # Repository 类
├── config/
│   └── dio_config.dart           # Dio 配置
└── pubspec_dependencies.yaml      # 依赖配置
```

## 生成的代码示例

### Dio Service 接口

```dart
import 'package:dio/dio.dart';
import 'com.example.api/models/response_data.dart';

abstract class ApiService {
  final Dio dio;

  ApiService(this.dio);

  /// 获取订单列表
  /// API: GET /api/orders
  Future<ResponseData<OrderListResponse>> getOrders({
    int? page,
    int? size,
  }) async {
    final response = await dio.get(
      '/api/orders',
      queryParameters: {
        'page': page,
        'size': size,
      },
    );
    return ResponseData<OrderListResponse>.fromJson(response.data);
  }
}
```

### Dart 实体类

```dart
import 'package:json_annotation/json_annotation.dart';

part 'order_response.g.dart';

@JsonSerializable()
class OrderResponse {
  final String orderId;
  final String userId;
  final double amount;
  final int? status;

  OrderResponse({
    required this.orderId,
    required this.userId,
    required this.amount,
    this.status,
  });

  factory OrderResponse.fromJson(Map<String, dynamic> json) =>
      _$OrderResponseFromJson(json);

  Map<String, dynamic> toJson() => _$OrderResponseToJson(this);
}
```

**注意**：
- 所有实体类都使用 `@JsonSerializable()` 注解
- 需要运行 `flutter pub run build_runner build` 生成 `.g.dart` 文件
- 字段名保持与服务器一致

### Repository 类

```dart
import 'com.example.api/models/response_data.dart';
import 'com.example.api/services/api_service.dart';

class ApiRepository {
  final ApiService apiService;

  ApiRepository(this.apiService);

  /// 获取订单列表
  Future<ResponseData<OrderListResponse>> getOrders({
    int? page,
    int? size,
  }) async {
    return await apiService.getOrders(page: page, size: size);
  }
}
```

### Dio 配置

```dart
import 'package:dio/dio.dart';
import 'com.example.api/services/api_service.dart';

class DioConfig {
  static const String baseUrl = 'https://api.example.com';
  static const int timeoutSeconds = 30;

  /// 创建 Dio 实例
  static Dio createDio() {
    final dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: Duration(seconds: timeoutSeconds),
      receiveTimeout: Duration(seconds: timeoutSeconds),
      sendTimeout: Duration(seconds: timeoutSeconds),
    ));

    return dio;
  }

  /// 创建 ApiService 实例
  static ApiService createApiService() {
    return ApiServiceImpl(createDio());
  }
}
```

## 配置选项

### FlutterCodeGenerator 参数

- `base_package` (str): Flutter 项目的基础包名，默认为 `"com.example.api"`
- `output_dir` (str): 输出目录，默认为 `"flutter_output"`

### 筛选分类

```python
# 生成特定分类的代码
generated_files = generator.generate(
    api_tree,
    category_filter="订单"  # 只生成"订单"分类下的 API
)
```

## 集成到 Flutter 项目

### 1. 添加依赖

在 `pubspec.yaml` 中添加以下依赖：

```yaml
dependencies:
  dio: ^5.4.0
  json_annotation: ^4.8.1

dev_dependencies:
  build_runner: ^2.4.7
  json_serializable: ^6.7.1
```

运行：
```bash
flutter pub get
```

### 2. 复制生成的代码

将生成的文件复制到你的 Flutter 项目中：
- `services/api_service.dart` → `lib/services/`
- `models/*.dart` → `lib/models/`
- `repositories/api_repository.dart` → `lib/repositories/`
- `config/dio_config.dart` → `lib/config/`

### 3. 生成序列化代码

运行以下命令生成 `.g.dart` 文件：

```bash
flutter pub run build_runner build
```

### 4. 使用生成的代码

```dart
import 'package:your_app/config/dio_config.dart';
import 'package:your_app/repositories/api_repository.dart';

class OrderViewModel {
  final ApiRepository repository;

  OrderViewModel() : repository = ApiRepository(DioConfig.createApiService());

  Future<void> loadOrders() async {
    final result = await repository.getOrders(page: 1, size: 20);
    if (result.code == 200) {
      // 处理数据
      print(result.data);
    } else {
      // 处理错误
      print(result.msg);
    }
  }
}
```

## 注意事项

1. **类型推断限制**: 当前版本的类型推断较为简单，可能需要手动调整生成的实体类
2. **API 路径参数**: 路径参数（如 `/api/users/{id}`）会自动转换为方法参数
3. **请求体类型**: 复杂请求体可能需要手动定义对应的 Dart 类
4. **响应包装**: 所有响应都使用 `ResponseData<T>` 统一包装格式（`{code, msg, data, hasNext}`）
5. **json_serializable**: 生成的实体类都使用 `json_serializable`，需要运行 `build_runner` 生成代码
6. **字段命名**: 实体类字段名保持与服务器一致，不进行转换

## 为 MCP 化做准备

本模块设计时已考虑 MCP（Model Context Protocol）集成：

- 模块化设计，易于作为 MCP 工具暴露
- 输入输出清晰，符合 MCP 工具规范
- 可扩展性强，方便添加新的代码生成功能

## 后续改进计划

- [ ] 支持自定义代码模板
- [ ] 支持多种 JSON 解析库（json_serializable、freezed 等）
- [ ] 支持响应包装类型自动识别
- [ ] 支持请求拦截器自动生成
- [ ] 支持多环境配置（开发、测试、生产）
- [ ] 生成单元测试代码模板

