"""
项目结构分析工具

提供项目文件树生成、项目分析等功能。
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from fnmatch import fnmatch

from .exceptions import FileOperationError
from .file_utils import get_file_info


# 默认排除的目录和文件
DEFAULT_EXCLUDE_DIRS = {
    ".git", ".svn", ".hg", "__pycache__", "node_modules", ".idea", ".vscode",
    "build", "dist", "target", ".gradle", ".mvn", "venv", "env", ".venv",
    ".pytest_cache", ".mypy_cache", ".tox", ".coverage", "htmlcov",
}

DEFAULT_EXCLUDE_FILES = {
    ".DS_Store", "Thumbs.db", ".gitignore", ".gitattributes",
}


def generate_file_tree(
    root_dir: str | Path,
    output_format: str = "text",
    exclude_dirs: Optional[Set[str]] = None,
    exclude_files: Optional[Set[str]] = None,
    include_hidden: bool = False,
    max_depth: Optional[int] = None,
) -> str | Dict[str, Any]:
    """
    生成项目文件树
    
    Args:
        root_dir: 根目录
        output_format: 输出格式（"text", "json", "markdown"）
        exclude_dirs: 要排除的目录名集合
        exclude_files: 要排除的文件名集合
        include_hidden: 是否包含隐藏文件/目录
        max_depth: 最大深度（None 表示无限制）
    
    Returns:
        文件树字符串或字典
    """
    root = Path(root_dir)
    
    if not root.exists() or not root.is_dir():
        raise FileOperationError(f"目录不存在: {root}")
    
    exclude_dirs = exclude_dirs or DEFAULT_EXCLUDE_DIRS
    exclude_files = exclude_files or DEFAULT_EXCLUDE_FILES
    
    tree_data = _build_tree(root, root, exclude_dirs, exclude_files, include_hidden, max_depth, 0)
    
    if output_format == "json":
        return json.dumps(tree_data, ensure_ascii=False, indent=2)
    elif output_format == "markdown":
        return _tree_to_markdown(tree_data)
    else:
        return _tree_to_text(tree_data)


def _build_tree(
    root: Path,
    current: Path,
    exclude_dirs: Set[str],
    exclude_files: Set[str],
    include_hidden: bool,
    max_depth: Optional[int],
    current_depth: int,
) -> Dict[str, Any]:
    """构建文件树数据结构"""
    if max_depth is not None and current_depth >= max_depth:
        return None
    
    name = current.name
    is_hidden = name.startswith(".")
    
    if not include_hidden and is_hidden and name not in {".git", ".gitignore"}:
        return None
    
    if current.is_file():
        if name in exclude_files:
            return None
        info = get_file_info(current)
        return {
            "name": name,
            "type": "file",
            "path": str(current.relative_to(root)),
            "size": info["size"],
        }
    elif current.is_dir():
        if name in exclude_dirs:
            return None
        
        children = []
        try:
            for item in sorted(current.iterdir()):
                child_tree = _build_tree(
                    root, item, exclude_dirs, exclude_files,
                    include_hidden, max_depth, current_depth + 1
                )
                if child_tree:
                    children.append(child_tree)
        except PermissionError:
            pass
        
        return {
            "name": name,
            "type": "directory",
            "path": str(current.relative_to(root)),
            "children": children,
        }
    
    return None


def _tree_to_text(tree: Dict[str, Any], prefix: str = "", is_last: bool = True) -> str:
    """将树结构转换为文本格式"""
    if tree is None:
        return ""
    
    name = tree["name"]
    connector = "└── " if is_last else "├── "
    result = prefix + connector + name + "\n"
    
    if tree["type"] == "directory" and tree.get("children"):
        children = tree["children"]
        extension = "    " if is_last else "│   "
        new_prefix = prefix + extension
        
        for i, child in enumerate(children):
            is_last_child = i == len(children) - 1
            result += _tree_to_text(child, new_prefix, is_last_child)
    
    return result


def _tree_to_markdown(tree: Dict[str, Any], level: int = 0) -> str:
    """将树结构转换为 Markdown 格式"""
    if tree is None:
        return ""
    
    indent = "  " * level
    name = tree["name"]
    
    if tree["type"] == "file":
        result = f"{indent}- `{name}`\n"
    else:
        result = f"{indent}- **{name}/**\n"
        if tree.get("children"):
            for child in tree["children"]:
                result += _tree_to_markdown(child, level + 1)
    
    return result


def analyze_project(
    root_dir: str | Path,
    exclude_dirs: Optional[Set[str]] = None,
    exclude_files: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    分析项目结构
    
    Args:
        root_dir: 项目根目录
        exclude_dirs: 要排除的目录名集合
        exclude_files: 要排除的文件名集合
    
    Returns:
        分析结果字典，包含：
        - total_files: 总文件数
        - total_dirs: 总目录数
        - total_size: 总大小（字节）
        - file_types: 文件类型统计
        - largest_files: 最大的文件列表
        - directory_structure: 目录结构
    """
    root = Path(root_dir)
    
    if not root.exists() or not root.is_dir():
        raise FileOperationError(f"目录不存在: {root}")
    
    exclude_dirs = exclude_dirs or DEFAULT_EXCLUDE_DIRS
    exclude_files = exclude_files or DEFAULT_EXCLUDE_FILES
    
    total_files = 0
    total_dirs = 0
    total_size = 0
    file_types = {}
    file_sizes = []
    
    def analyze_directory(dir_path: Path):
        nonlocal total_files, total_dirs, total_size
        
        try:
            for item in dir_path.iterdir():
                if item.name in exclude_dirs or item.name in exclude_files:
                    continue
                
                if item.is_file():
                    total_files += 1
                    info = get_file_info(item)
                    size = info["size"]
                    total_size += size
                    
                    # 统计文件类型
                    ext = item.suffix.lower() or "no_extension"
                    file_types[ext] = file_types.get(ext, 0) + 1
                    
                    # 记录文件大小
                    file_sizes.append({
                        "path": str(item.relative_to(root)),
                        "size": size,
                    })
                
                elif item.is_dir():
                    if item.name not in exclude_dirs:
                        total_dirs += 1
                        analyze_directory(item)
        except PermissionError:
            pass
    
    analyze_directory(root)
    
    # 排序找出最大的文件
    file_sizes.sort(key=lambda x: x["size"], reverse=True)
    largest_files = file_sizes[:10]
    
    return {
        "total_files": total_files,
        "total_dirs": total_dirs,
        "total_size": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "file_types": file_types,
        "largest_files": largest_files,
    }

