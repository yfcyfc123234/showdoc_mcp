"""
文件查找和搜索工具
"""

import re
from pathlib import Path
from typing import List, Optional, Callable, Generator, Pattern, Dict, Any
from fnmatch import fnmatch

from .exceptions import FileOperationError
from .content_processor import read_file_safe


def find_files(
    directory: str | Path,
    pattern: Optional[str] = None,
    extension: Optional[str] = None,
    recursive: bool = True,
    case_sensitive: bool = False,
) -> List[Path]:
    """
    查找文件
    
    Args:
        directory: 搜索目录
        pattern: 文件名模式（支持通配符，如 "*.py"）
        extension: 文件扩展名（如 ".py"）
        recursive: 是否递归搜索
        case_sensitive: 是否区分大小写
    
    Returns:
        找到的文件路径列表
    """
    dir_path = Path(directory)
    
    if not dir_path.exists() or not dir_path.is_dir():
        return []
    
    files = []
    
    if recursive:
        search_paths = dir_path.rglob("*")
    else:
        search_paths = dir_path.glob("*")
    
    for path in search_paths:
        if not path.is_file():
            continue
        
        # 检查扩展名
        if extension:
            if not case_sensitive:
                if not path.suffix.lower() == extension.lower():
                    continue
            else:
                if not path.suffix == extension:
                    continue
        
        # 检查文件名模式
        if pattern:
            if not case_sensitive:
                if not fnmatch(path.name.lower(), pattern.lower()):
                    continue
            else:
                if not fnmatch(path.name, pattern):
                    continue
        
        files.append(path)
    
    return files


def search_content(
    directory: str | Path,
    search_text: str | Pattern,
    pattern: Optional[str] = None,
    extension: Optional[str] = None,
    recursive: bool = True,
    regex: bool = False,
    case_sensitive: bool = False,
    encoding: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    搜索文件内容
    
    Args:
        directory: 搜索目录
        search_text: 要搜索的文本或正则表达式
        pattern: 文件名模式（只搜索匹配的文件）
        extension: 文件扩展名
        recursive: 是否递归搜索
        regex: 是否使用正则表达式
        case_sensitive: 是否区分大小写
        encoding: 文件编码（None 则自动检测）
    
    Returns:
        搜索结果列表，每个结果包含：
        - file: 文件路径
        - matches: 匹配信息列表，每个匹配包含：
          - line_number: 行号
          - line_content: 行内容
          - match_text: 匹配的文本
    """
    dir_path = Path(directory)
    
    if not dir_path.exists() or not dir_path.is_dir():
        return []
    
    # 准备搜索模式
    if regex:
        if isinstance(search_text, str):
            flags = 0 if case_sensitive else re.IGNORECASE
            search_pattern = re.compile(search_text, flags)
        else:
            search_pattern = search_text
    else:
        if not case_sensitive:
            search_text_lower = search_text.lower() if isinstance(search_text, str) else None
        else:
            search_text_lower = None
    
    # 查找文件
    files = find_files(dir_path, pattern=pattern, extension=extension, recursive=recursive)
    
    results = []
    
    for file_path in files:
        try:
            # 读取文件内容
            content = read_file_safe(file_path, encoding=encoding)
            lines = content.splitlines()
            
            matches = []
            for line_num, line in enumerate(lines, 1):
                if regex:
                    for match in search_pattern.finditer(line):
                        matches.append({
                            "line_number": line_num,
                            "line_content": line,
                            "match_text": match.group(),
                            "start": match.start(),
                            "end": match.end(),
                        })
                else:
                    if case_sensitive:
                        if search_text in line:
                            matches.append({
                                "line_number": line_num,
                                "line_content": line,
                                "match_text": search_text,
                            })
                    else:
                        if search_text_lower and search_text_lower in line.lower():
                            matches.append({
                                "line_number": line_num,
                                "line_content": line,
                                "match_text": search_text,
                            })
            
            if matches:
                results.append({
                    "file": str(file_path),
                    "matches": matches,
                })
        except Exception:
            # 跳过无法读取的文件
            continue
    
    return results


def filter_files(
    file_paths: List[str | Path],
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    extension: Optional[str] = None,
    pattern: Optional[str] = None,
    custom_filter: Optional[Callable[[Path], bool]] = None,
) -> List[Path]:
    """
    过滤文件列表
    
    Args:
        file_paths: 文件路径列表
        min_size: 最小文件大小（字节）
        max_size: 最大文件大小（字节）
        extension: 文件扩展名
        pattern: 文件名模式
        custom_filter: 自定义过滤函数
    
    Returns:
        过滤后的文件路径列表
    """
    filtered = []
    
    for file_path in file_paths:
        path = Path(file_path)
        
        if not path.exists() or not path.is_file():
            continue
        
        # 检查文件大小
        if min_size is not None or max_size is not None:
            size = path.stat().st_size
            if min_size is not None and size < min_size:
                continue
            if max_size is not None and size > max_size:
                continue
        
        # 检查扩展名
        if extension:
            if not path.suffix.lower() == extension.lower():
                continue
        
        # 检查文件名模式
        if pattern:
            if not fnmatch(path.name, pattern):
                continue
        
        # 自定义过滤
        if custom_filter:
            if not custom_filter(path):
                continue
        
        filtered.append(path)
    
    return filtered

