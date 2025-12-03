# 压缩解压工具模块

提供 ZIP、7Z、RAR 格式的压缩和解压功能，支持密码保护、分卷压缩等高级功能。

## 功能特性

### 支持的格式
- **ZIP**: 使用 `pyzipper`（支持真正的 AES 密码保护），如果未安装则回退到标准库 `zipfile`（密码保护有限）
- **7Z**: 使用 `py7zr`（纯 Python 实现）
- **RAR**: 使用 `rarfile`（需要系统安装 unrar 工具）

### 压缩功能
- 支持单个文件、多个文件、目录压缩
- 压缩级别（0-9，对应"速度最快"到"体积最小"）
- 密码保护（**ZIP 格式**：如果安装了 `pyzipper`，支持真正的 AES 密码保护；否则使用标准库，密码保护有限）
- 分卷压缩（参数已预留，但当前使用的 `py7zr` 不支持真正的 7Z 分卷压缩，会返回明确错误提示；如需分卷请使用外部 7z.exe 或 WinRAR）
- 压缩后删除源文件
- 直接存储压缩率低的文件
- 压缩每个文件到单独的压缩包

### 解压功能
- 支持所有格式的解压
- 密码解压
- 指定解压目录
- 解压后删除压缩包

## 使用方法

### Python 代码调用

```python
from archive_tools import compress_files, extract_archive

# 压缩文件
result = compress_files(
    source_paths=["file1.txt", "file2.txt", "directory/"],
    output_path="output.zip",
    format="zip",
    compression_level=6,
    password="mypassword",
    delete_source=False,
)

# 解压文件
result = extract_archive(
    archive_path="output.zip",
    output_dir="extracted/",
    password="mypassword",
)
```

### MCP 工具调用

在 Cursor 中通过 MCP 工具调用：

1. **compress_files_tool** - 压缩文件
2. **extract_archive_tool** - 解压文件

## 依赖要求

### Python 包
- `pyzipper>=0.3.6` - ZIP 格式增强支持（真正的 AES 密码保护，推荐安装）
- `py7zr>=0.21.0` - 7Z 格式支持
- `rarfile>=4.1` - RAR 格式支持

### 系统工具（仅 RAR 格式需要）

**Windows:**
- 需要 `unrar.exe` 在系统 PATH 中
- 可以从 [WinRAR 官网](https://www.winrar.com/) 下载

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install unrar

# CentOS/RHEL
sudo yum install unrar
```

**macOS:**
```bash
brew install unrar
```

## 测试

### 运行测试

```bash
# 方式 1: 在 archive_tools 目录内运行
cd archive_tools
python test.py

# 方式 2: 从项目根目录运行
python -m archive_tools.test
```

**测试结果自动保存**：

测试完成后，所有测试结果会自动保存到 `archive_tools/test_results.md` 文件中，方便查看和分享。

- 测试结果包含完整的测试输出
- 包含测试时间和完成时间
- 包含所有测试用例的执行结果
- 可以直接查看该文件了解测试详情

### 测试内容

测试脚本会测试以下功能：

1. **ZIP 格式压缩和解压** - 基础功能测试
2. **密码保护** - 压缩和解压密码保护
3. **7Z 格式** - 7Z 格式压缩和解压（如果 py7zr 已安装）
4. **压缩级别** - 不同压缩级别（0-9）的效果对比
5. **单独压缩** - 每个文件单独压缩功能
6. **RAR 解压** - RAR 格式解压（如果有 RAR 文件）
7. **错误处理** - 各种错误情况的处理

### 测试配置

在 `test.py` 中可以配置：

```python
# 是否自动清理测试文件
AUTO_CLEANUP = True

# 是否显示详细信息
SHOW_DETAILS = True

# 是否保存测试结果到文档
SAVE_RESULTS_TO_FILE = True

# 测试结果保存路径（相对于项目根目录）
RESULTS_FILE_PATH = "archive_tools/test_results.md"
```

**测试结果文件**：

- 默认保存到：`archive_tools/test_results.md`
- 格式：Markdown 格式，包含完整的测试输出
- 内容：测试时间、所有测试用例结果、完成时间等
- 用途：方便查看测试结果、分享给他人、记录测试历史

## 注意事项

1. **ZIP 密码保护**：
   - **推荐**：安装 `pyzipper` 库，提供真正的 AES 密码保护
   - **备选**：如果未安装 `pyzipper`，将使用标准库 `zipfile`（密码保护有限，错误密码也可能解压）
   - 安装方法：`pip install pyzipper`

2. **RAR 格式限制**：rarfile 需要系统安装 unrar 工具，如果未安装，RAR 格式将不可用。另外，RAR 格式的创建需要外部工具（WinRAR 或 rar），本工具仅支持 RAR 格式的解压。

3. **跨平台兼容**：所有路径处理使用 `pathlib`，确保跨平台兼容

4. **大文件处理**：使用流式处理，避免内存溢出

5. **错误处理**：提供清晰的错误信息，特别是格式不支持或工具缺失的情况

6. **分卷压缩**：
   - 当前 `py7zr` 库**不支持真正的分卷压缩**，调用分卷功能会返回明确错误提示
   - 如需分卷压缩，请使用外部 7z 工具（如 `7z.exe`）或 WinRAR 等工具
   - ZIP 格式的分卷同样需要使用外部工具创建

