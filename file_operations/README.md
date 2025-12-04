# File Operations 模块

提供完整的文件操作功能，包括基础文件操作、批量操作、内容处理、代码操作、项目分析、Git 集成等功能。

## 功能特性

### 基础文件操作
- 文件/目录复制、移动、删除
- 文件/目录创建（递归）
- 文件重命名
- 文件存在性检查
- 文件权限设置（跨平台）

### 批量文件操作
- 批量复制/移动/删除（支持通配符）
- 批量重命名（支持规则和模板）
- 批量文件内容替换（支持正则）
- 进度显示和中断处理

### 文件查找和搜索
- 按名称/扩展名查找
- 按内容搜索（支持正则）
- 按大小/修改时间筛选
- 递归目录搜索

### 文件内容处理
- 安全读取/写入（支持编码）
- 文件内容替换（单文件/批量）
- 文件合并/分割
- 行级操作（追加、删除、插入）
- 文件编码检测和转换

### 代码块操作
- 在文件中插入代码块（指定位置：行号、标记、函数内）
- 替换代码块（按行号范围或标记）
- 删除代码块（按行号范围或标记）
- 提取代码块到新文件
- 查找代码块（按函数名、类名、注释标记）

### 模板文件生成
- 从模板生成文件（支持变量替换）
- 批量从模板生成多个文件
- 模板变量替换（支持字典、环境变量）

### 项目结构分析
- 生成项目文件树（文本、JSON、Markdown）
- 过滤特定文件类型
- 排除目录（.git、node_modules 等）
- 统计文件数量和大小

### 依赖关系分析
- 解析导入语句（Python、Dart、Kotlin、Java 等）
- 查找文件引用（哪些文件引用了某个文件）
- 查找未使用的文件
- 构建依赖图

### Git 集成
- 检查文件是否在 Git 中
- 获取文件 Git 状态（新增、修改、删除）
- 检查文件是否被忽略（`.gitignore`）
- 自动添加文件到 Git（根据规则）
- 批量添加文件到 Git

### 文件格式处理
- JSON 读写（带格式化、错误处理）
- YAML 读写
- XML 读写
- TOML 读写
- Markdown 处理（解析、提取、生成目录）

### 文件差异和比较
- 文件内容差异（行级、字符级）
- 目录差异（新增、删除、修改的文件）
- 文件哈希比较
- 生成差异报告

### 文件内容分析
- 代码行数统计（总行数、空行、注释、代码行）
- 文件大小分析
- 字符/单词统计
- 全文搜索（支持正则、多文件搜索）

### 临时文件管理
- 创建临时文件/目录（自动清理）
- 带上下文的临时文件（命名规范）
- 临时文件生命周期管理

### 文件备份和恢复
- 自动备份（写入前备份）
- 带时间戳的备份
- 备份管理（保留策略）
- 从备份恢复

### 文件验证和检查
- 文件编码检测和转换
- 文件格式验证
- 文件大小检查
- 文件权限检查
- 查找大文件、空文件、重复文件

### 路径和引用处理
- 解析导入路径（相对路径转绝对路径）
- 查找文件引用（更新导入路径）
- 路径规范化
- 跨平台路径处理
- 批量更新导入路径

## 使用方法

### Python 代码调用

```python
from file_operations import (
    copy_file,
    read_file_safe,
    write_file_safe,
    find_files,
    search_content,
    generate_from_template,
)

# 基础文件操作
copy_file("source.txt", "dest.txt")

# 读取文件
content = read_file_safe("file.txt")

# 写入文件
write_file_safe("file.txt", "content")

# 查找文件
files = find_files(".", pattern="*.py", recursive=True)

# 搜索内容
results = search_content(".", "import os", pattern="*.py")

# 从模板生成文件
generate_from_template("template.txt", "output.txt", variables={"name": "test"})
```

### MCP 工具使用

所有功能都已封装为 MCP 工具，可以在 Cursor 等 MCP 客户端中使用。

#### 基础文件操作

- `mcp_file_create`: 创建文件
- `mcp_file_read`: 读取文件
- `mcp_file_update`: 更新文件
- `mcp_file_delete`: 删除文件
- `mcp_file_copy`: 复制文件
- `mcp_file_move`: 移动文件
- `mcp_file_rename`: 重命名文件
- `mcp_file_get_info`: 获取文件信息

#### 批量操作

- `mcp_file_create_batch`: 批量创建文件
- `mcp_file_read_batch`: 批量读取文件
- `mcp_file_update_batch`: 批量更新文件
- `mcp_file_delete_batch`: 批量删除文件

#### 目录操作

- `mcp_file_list_directory`: 列出目录内容
- `mcp_file_create_directory`: 创建目录
- `mcp_file_search_files`: 搜索文件

#### 高级功能

- `mcp_file_search_content`: 搜索文件内容
- `mcp_file_replace_content`: 替换文件内容
- `mcp_file_compare`: 比较文件
- `mcp_file_analyze_project`: 分析项目结构
- `mcp_file_generate_from_template`: 从模板生成文件
- `mcp_file_git_status`: 获取 Git 状态
- `mcp_file_backup`: 备份文件

## 依赖要求

- Python >= 3.9
- chardet >= 5.0.0（用于编码检测）

可选依赖：
- PyYAML（用于 YAML 处理）
- tomli / tomli-w（用于 TOML 处理）

## 注意事项

1. **跨平台兼容**: 使用 `pathlib.Path` 处理路径，支持 Windows、Linux、Mac
2. **编码处理**: 自动检测文件编码，支持多种编码格式
3. **错误处理**: 统一的异常处理和错误信息
4. **性能优化**: 大文件/大批量操作使用生成器，避免内存占用
5. **安全性**: 操作前检查权限，支持只读模式

## 许可证

本项目为内部工具，仅供团队使用。

