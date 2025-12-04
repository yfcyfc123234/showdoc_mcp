"""
文件验证和检查工具

提供文件编码检测、格式验证、文件查找等功能。
"""

import chardet
from pathlib import Path
from typing import List, Optional, Dict, Any
from collections import defaultdict

# 使用内置异常
from .file_utils import get_file_info


def detect_encoding(
    file_path: str | Path,
    sample_size: int = 10000,
) -> Dict[str, Any]:
    """
    检测文件编码
    
    Args:
        file_path: 文件路径
        sample_size: 采样大小（字节）
    
    Returns:
        编码信息字典，包含：
        - encoding: 检测到的编码
        - confidence: 置信度（0-1）
        - language: 语言（如果可检测）
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    try:
        with open(path, "rb") as f:
            sample = f.read(sample_size)
        
        result = chardet.detect(sample)
        
        return {
            "encoding": result.get("encoding", "unknown"),
            "confidence": result.get("confidence", 0.0),
            "language": result.get("language", None),
        }
    except Exception as e:
        return {
            "encoding": "unknown",
            "confidence": 0.0,
            "language": None,
            "error": str(e),
        }


def convert_encoding(
    file_path: str | Path,
    target_encoding: str = "utf-8",
    source_encoding: Optional[str] = None,
    backup: bool = True,
) -> Path:
    """
    转换文件编码
    
    Args:
        file_path: 文件路径
        target_encoding: 目标编码
        source_encoding: 源编码（如果为 None 则自动检测）
        backup: 是否备份原文件
    
    Returns:
        文件路径
    
    Raises:
        FileNotFoundError: 文件不存在
        EncodingError: 编码转换失败
    """
    from .exceptions import EncodingError
    from .content_processor import read_file_safe
    from .safe_writer import SafeFileWriter
    
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    # 检测源编码
    if source_encoding is None:
        encoding_info = detect_encoding(path)
        source_encoding = encoding_info.get("encoding", "utf-8")
    
    # 读取文件
    try:
        content = read_file_safe(path, encoding=source_encoding)
    except Exception as e:
        raise EncodingError(f"读取文件失败: {e}")
    
    # 写入新编码
    writer = SafeFileWriter(path, encoding=target_encoding, backup=backup)
    writer.write(content)
    
    return path


def find_large_files(
    directory: str | Path,
    min_size: int,
    recursive: bool = True,
) -> List[Dict[str, Any]]:
    """
    查找大文件
    
    Args:
        directory: 搜索目录
        min_size: 最小文件大小（字节）
        recursive: 是否递归搜索
    
    Returns:
        大文件列表，每个文件包含：
        - path: 文件路径
        - size: 文件大小（字节）
        - size_mb: 文件大小（MB）
    """
    dir_path = Path(directory)
    
    if not dir_path.exists() or not dir_path.is_dir():
        return []
    
    large_files = []
    
    if recursive:
        search_paths = dir_path.rglob("*")
    else:
        search_paths = dir_path.glob("*")
    
    for path in search_paths:
        if not path.is_file():
            continue
        
        try:
            size = path.stat().st_size
            if size >= min_size:
                large_files.append({
                    "path": str(path),
                    "size": size,
                    "size_mb": round(size / (1024 * 1024), 2),
                })
        except Exception:
            continue
    
    # 按大小排序
    large_files.sort(key=lambda x: x["size"], reverse=True)
    
    return large_files


def find_empty_files(
    directory: str | Path,
    recursive: bool = True,
) -> List[Path]:
    """
    查找空文件
    
    Args:
        directory: 搜索目录
        recursive: 是否递归搜索
    
    Returns:
        空文件路径列表
    """
    dir_path = Path(directory)
    
    if not dir_path.exists() or not dir_path.is_dir():
        return []
    
    empty_files = []
    
    if recursive:
        search_paths = dir_path.rglob("*")
    else:
        search_paths = dir_path.glob("*")
    
    for path in search_paths:
        if not path.is_file():
            continue
        
        try:
            if path.stat().st_size == 0:
                empty_files.append(path)
        except Exception:
            continue
    
    return empty_files


def find_duplicate_files(
    directory: str | Path,
    recursive: bool = True,
) -> List[List[Path]]:
    """
    查找重复文件（基于内容哈希）
    
    Args:
        directory: 搜索目录
        recursive: 是否递归搜索
    
    Returns:
        重复文件组列表，每个组包含内容相同的文件路径列表
    """
    from .file_comparison import get_file_hash
    
    dir_path = Path(directory)
    
    if not dir_path.exists() or not dir_path.is_dir():
        return []
    
    # 收集所有文件及其哈希
    file_hashes = defaultdict(list)
    
    if recursive:
        search_paths = dir_path.rglob("*")
    else:
        search_paths = dir_path.glob("*")
    
    for path in search_paths:
        if not path.is_file():
            continue
        
        try:
            file_hash = get_file_hash(path)
            file_hashes[file_hash].append(path)
        except Exception:
            continue
    
    # 找出重复的文件组（哈希值相同的文件）
    duplicate_groups = [files for files in file_hashes.values() if len(files) > 1]
    
    return duplicate_groups

