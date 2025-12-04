"""
文件差异和比较工具
"""

import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from difflib import unified_diff, context_diff

# 使用内置异常
from .content_processor import read_file_safe
from .file_utils import get_file_info


def get_file_hash(
    file_path: str | Path,
    algorithm: str = "md5",
) -> str:
    """
    计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法（"md5", "sha1", "sha256"）
    
    Returns:
        哈希值字符串
    
    Raises:
        FileNotFoundError: 文件不存在
        FileOperationError: 哈希计算失败
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    if not path.is_file():
        raise FileOperationError(f"路径不是文件: {path}")
    
    hash_obj = hashlib.new(algorithm)
    
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        raise FileOperationError(f"计算文件哈希失败: {e}")


def compare_files(
    file1_path: str | Path,
    file2_path: str | Path,
    diff_format: str = "unified",
    context_lines: int = 3,
) -> Dict[str, Any]:
    """
    比较两个文件
    
    Args:
        file1_path: 第一个文件路径
        file2_path: 第二个文件路径
        diff_format: 差异格式（"unified", "context"）
        context_lines: 上下文行数
    
    Returns:
        比较结果字典，包含：
        - are_identical: 是否完全相同
        - hash1: 文件1的哈希值
        - hash2: 文件2的哈希值
        - diff: 差异内容
        - diff_lines: 差异行数统计
    """
    path1 = Path(file1_path)
    path2 = Path(file2_path)
    
    if not path1.exists():
        raise FileNotFoundError(f"文件不存在: {path1}")
    if not path2.exists():
        raise FileNotFoundError(f"文件不存在: {path2}")
    
    # 计算哈希
    hash1 = get_file_hash(path1)
    hash2 = get_file_hash(path2)
    
    are_identical = hash1 == hash2
    
    if are_identical:
        return {
            "are_identical": True,
            "hash1": hash1,
            "hash2": hash2,
            "diff": "",
            "diff_lines": {"added": 0, "removed": 0, "modified": 0},
        }
    
    # 读取文件内容
    content1 = read_file_safe(path1)
    content2 = read_file_safe(path2)
    
    lines1 = content1.splitlines(keepends=True)
    lines2 = content2.splitlines(keepends=True)
    
    # 生成差异
    if diff_format == "context":
        diff_lines = list(context_diff(
            lines1, lines2,
            fromfile=str(path1),
            tofile=str(path2),
            lineterm="",
            n=context_lines,
        ))
    else:
        diff_lines = list(unified_diff(
            lines1, lines2,
            fromfile=str(path1),
            tofile=str(path2),
            lineterm="",
            n=context_lines,
        ))
    
    diff_text = "".join(diff_lines)
    
    # 统计差异行数
    added = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))
    modified = min(added, removed)
    
    return {
        "are_identical": False,
        "hash1": hash1,
        "hash2": hash2,
        "diff": diff_text,
        "diff_lines": {
            "added": added - modified,
            "removed": removed - modified,
            "modified": modified,
        },
    }


def compare_directories(
    dir1_path: str | Path,
    dir2_path: str | Path,
    ignore_patterns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    比较两个目录
    
    Args:
        dir1_path: 第一个目录路径
        dir2_path: 第二个目录路径
        ignore_patterns: 要忽略的文件/目录模式列表
    
    Returns:
        比较结果字典，包含：
        - only_in_dir1: 只在目录1中的文件
        - only_in_dir2: 只在目录2中的文件
        - different_files: 内容不同的文件
        - identical_files: 内容相同的文件
    """
    dir1 = Path(dir1_path)
    dir2 = Path(dir2_path)
    
    if not dir1.exists() or not dir1.is_dir():
        raise FileNotFoundError(f"目录不存在: {dir1}")
    if not dir2.exists() or not dir2.is_dir():
        raise FileNotFoundError(f"目录不存在: {dir2}")
    
    ignore_patterns = ignore_patterns or []
    
    def should_ignore(path: Path) -> bool:
        """检查是否应该忽略"""
        for pattern in ignore_patterns:
            if pattern in str(path):
                return True
        return False
    
    # 收集所有文件
    files1 = {f.relative_to(dir1): f for f in dir1.rglob("*") if f.is_file() and not should_ignore(f)}
    files2 = {f.relative_to(dir2): f for f in dir2.rglob("*") if f.is_file() and not should_ignore(f)}
    
    all_files = set(files1.keys()) | set(files2.keys())
    
    only_in_dir1 = []
    only_in_dir2 = []
    different_files = []
    identical_files = []
    
    for rel_path in all_files:
        if rel_path not in files1:
            only_in_dir2.append(str(rel_path))
        elif rel_path not in files2:
            only_in_dir1.append(str(rel_path))
        else:
            # 比较文件内容
            try:
                hash1 = get_file_hash(files1[rel_path])
                hash2 = get_file_hash(files2[rel_path])
                
                if hash1 == hash2:
                    identical_files.append(str(rel_path))
                else:
                    different_files.append(str(rel_path))
            except Exception:
                # 如果无法比较，标记为不同
                different_files.append(str(rel_path))
    
    return {
        "only_in_dir1": only_in_dir1,
        "only_in_dir2": only_in_dir2,
        "different_files": different_files,
        "identical_files": identical_files,
    }

