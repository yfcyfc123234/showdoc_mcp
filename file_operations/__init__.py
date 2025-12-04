"""
File Operations 模块

提供完整的文件操作功能，包括基础文件操作、批量操作、内容处理、代码操作、
项目分析、Git 集成等功能。
"""

__version__ = "1.0.0"

# 导出主要接口
from .exceptions import (
    FileOperationError,
    EncodingError,
    TemplateError,
    InvalidPathError,
    OperationCancelledError,
    BackupError,
    GitOperationError,
)

from .file_utils import (
    copy_file,
    move_file,
    delete_file,
    create_file,
    create_directory,
    rename_file,
    file_exists,
    get_file_info,
)

from .safe_writer import SafeFileWriter

from .content_processor import (
    read_file_safe,
    write_file_safe,
    replace_content,
    merge_files,
    split_file,
)

from .code_operations import (
    insert_code_block,
    replace_code_block,
    delete_code_block,
    extract_code_block,
    find_code_block,
)

from .template_engine import (
    generate_from_template,
    generate_batch_from_template,
)

from .file_search import (
    find_files,
    search_content,
    filter_files,
)

from .batch_operations import (
    batch_copy,
    batch_move,
    batch_delete,
    batch_rename,
    batch_replace_content,
)

from .project_analyzer import (
    generate_file_tree,
    analyze_project,
)

from .dependency_analyzer import (
    parse_imports,
    find_file_references,
    find_unused_files,
    build_dependency_graph,
)

from .git_integration import (
    is_file_tracked,
    get_file_git_status,
    is_file_ignored,
    add_file_to_git,
    batch_add_to_git,
)

from .format_handlers import (
    read_json,
    write_json,
    read_yaml,
    write_yaml,
    read_xml,
    write_xml,
    read_toml,
    write_toml,
)

from .file_comparison import (
    compare_files,
    compare_directories,
    get_file_hash,
)

from .content_analyzer import (
    count_lines,
    analyze_file_size,
    search_text,
)

from .temp_manager import (
    create_temp_file,
    create_temp_directory,
)

from .backup_manager import (
    backup_file,
    restore_file,
)

from .file_validator import (
    detect_encoding,
    convert_encoding,
    find_large_files,
    find_empty_files,
    find_duplicate_files,
)

from .path_resolver import (
    resolve_import_path,
    find_file_references_by_path,
    normalize_path,
    update_import_paths,
)

__all__ = [
    # 版本
    "__version__",
    # 异常
    "FileOperationError",
    "EncodingError",
    "TemplateError",
    "InvalidPathError",
    "OperationCancelledError",
    "BackupError",
    "GitOperationError",
    # 基础文件操作
    "copy_file",
    "move_file",
    "delete_file",
    "create_file",
    "create_directory",
    "rename_file",
    "file_exists",
    "get_file_info",
    # 智能写入
    "SafeFileWriter",
    # 内容处理
    "read_file_safe",
    "write_file_safe",
    "replace_content",
    "merge_files",
    "split_file",
    # 代码操作
    "insert_code_block",
    "replace_code_block",
    "delete_code_block",
    "extract_code_block",
    "find_code_block",
    # 模板引擎
    "generate_from_template",
    "generate_batch_from_template",
    # 文件搜索
    "find_files",
    "search_content",
    "filter_files",
    # 批量操作
    "batch_copy",
    "batch_move",
    "batch_delete",
    "batch_rename",
    "batch_replace_content",
    # 项目分析
    "generate_file_tree",
    "analyze_project",
    # 依赖分析
    "parse_imports",
    "find_file_references",
    "find_unused_files",
    "build_dependency_graph",
    # Git 集成
    "is_file_tracked",
    "get_file_git_status",
    "is_file_ignored",
    "add_file_to_git",
    "batch_add_to_git",
    # 格式处理
    "read_json",
    "write_json",
    "read_yaml",
    "write_yaml",
    "read_xml",
    "write_xml",
    "read_toml",
    "write_toml",
    # 文件比较
    "compare_files",
    "compare_directories",
    "get_file_hash",
    # 内容分析
    "count_lines",
    "analyze_file_size",
    "search_text",
    # 临时文件
    "create_temp_file",
    "create_temp_directory",
    # 备份恢复
    "backup_file",
    "restore_file",
    # 文件验证
    "detect_encoding",
    "convert_encoding",
    "find_large_files",
    "find_empty_files",
    "find_duplicate_files",
    # 路径处理
    "resolve_import_path",
    "find_file_references_by_path",
    "normalize_path",
    "update_import_paths",
]

