# Android 代码生成器架构说明

## 设计目标

将 core 模块从 ShowDoc 获取的 API 数据自动转换为 Android 项目可用的代码，为后续 MCP（Model Context Protocol）集成做准备。

## 模块结构

```
android_codegen/
├── __init__.py              # 模块导出
├── generator.py             # 主生成器（整合各个生成器）
├── retrofit_generator.py    # Retrofit Service 生成器
├── entity_generator.py      # 实体类生成器
├── okhttp_config.py         # OkHttp 配置生成器
├── test.py                  # 测试脚本
├── requirements.txt         # 依赖说明
├── README.md                # 使用文档
├── README_测试.md           # 测试说明文档
└── ARCHITECTURE.md          # 本文档
```

## 设计原则

### 1. 模块化设计

每个生成器独立实现，职责单一：
- `RetrofitServiceGenerator`: 专注于生成 Retrofit 接口
- `AndroidEntityGenerator`: 专注于生成实体类
- `OkHttpConfigGenerator`: 专注于生成配置代码
- `AndroidCodeGenerator`: 整合所有生成器，提供统一接口

### 2. 清晰的输入输出

**输入**: `ApiTree` 对象（来自 core 模块）
**输出**: 生成的文件路径字典

```python
{
    "services": ["path/to/ApiService.kt"],
    "entities": ["path/to/Entity1.kt", ...],
    "config": ["path/to/OkHttpConfig.kt", ...]
}
```

### 3. 可扩展性

- 易于添加新的代码生成器
- 易于支持不同的代码生成目标（如 iOS、前端等）
- 易于自定义代码模板

## 为 MCP 化做准备

### MCP 工具接口设计

未来可以作为 MCP 工具暴露，提供以下能力：

#### 1. 生成 Android 代码工具

```python
def mcp_generate_android_code(
    base_url: str,
    cookie: str,
    node_name: Optional[str] = None,
    base_package: str = "com.example.api",
    output_dir: str = "android_output"
) -> Dict[str, Any]:
    """
    MCP 工具：生成 Android 代码
    
    参数:
        base_url: ShowDoc 文档 URL
        cookie: 认证 Cookie
        node_name: 可选的节点名称过滤
        base_package: Android 包名
        output_dir: 输出目录
    
    返回:
        {
            "success": bool,
            "files": {
                "services": [...],
                "entities": [...],
                "config": [...]
            },
            "message": str
        }
    """
    # 实现逻辑
```

#### 2. 工具描述

```json
{
    "name": "generate_android_code",
    "description": "从 ShowDoc 文档生成 Android Retrofit Service 接口、实体类和配置",
    "inputSchema": {
        "type": "object",
        "properties": {
            "base_url": {"type": "string", "description": "ShowDoc 文档 URL"},
            "cookie": {"type": "string", "description": "认证 Cookie"},
            "node_name": {"type": "string", "description": "可选的节点名称过滤"},
            "base_package": {"type": "string", "description": "Android 包名"},
            "output_dir": {"type": "string", "description": "输出目录"}
        },
        "required": ["base_url", "cookie"]
    }
}
```

### 当前实现的优势

1. **输入标准化**: 使用 core 模块的标准输出（`ApiTree`），便于与其他工具集成
2. **输出结构化**: 返回生成文件路径的字典，便于 MCP 工具向用户报告结果
3. **错误处理**: 可以在 MCP 层面统一处理异常，返回友好的错误信息
4. **可配置性**: 支持多种配置选项（包名、输出目录等），便于适配不同项目

### 下一步改进

1. **增强类型推断**: 
   - 从 ShowDoc 响应示例中更准确地推断类型
   - 支持嵌套对象和数组类型

2. **支持更多 Android 特性**:
   - Room 数据库实体类生成
   - ViewModel 和 Repository 模板生成
   - 依赖注入模块生成（Koin、Hilt 等）

3. **模板系统**:
   - 支持自定义代码模板
   - 支持不同的代码风格（如 Google 风格、自定义风格）

4. **MCP 集成**:
   - 添加 MCP 工具接口
   - 实现工具注册和调用机制
   - 添加错误处理和日志记录

5. **多平台支持**:
   - iOS（Swift + URLSession）
   - 前端（TypeScript + Axios）
   - 其他平台...

## 使用流程

```
ShowDoc URL + Cookie
    ↓
core 模块（ShowDocClient）
    ↓
ApiTree 对象
    ↓
android_codegen 模块（AndroidCodeGenerator）
    ↓
Android 代码文件（.kt）
    ↓
集成到 Android 项目
```

## 依赖关系

```
android_codegen
    └── core (ShowDocClient, ApiTree, models)
            └── requests, json, html
```

## 测试建议

1. **单元测试**: 为每个生成器编写单元测试
2. **集成测试**: 测试从 ShowDoc 获取数据到生成代码的完整流程
3. **代码质量**: 验证生成的代码是否符合 Kotlin 规范

## 注意事项

1. **类型推断限制**: 当前类型推断较为简单，可能需要手动调整生成的代码
2. **API 路径参数**: 确保路径参数格式正确（如 `/api/users/{id}`）
3. **响应包装**: 如果 API 有统一的响应包装格式，需要特殊处理
4. **代码风格**: 生成的代码可能需要根据项目规范进行调整

