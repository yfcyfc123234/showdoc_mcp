"""
批量文件操作工具

支持批量复制、移动、删除、重命名等操作，带进度显示和中断处理。
"""

import signal
import sys
import shutil
import re
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any, Generator
from fnmatch import fnmatch

from .exceptions import FileOperationError, OperationCancelledError
from .file_utils import copy_file, move_file, delete_file, rename_file
from .content_processor import replace_content


# 全局中断标志
_interrupted = False


def _signal_handler(sig, frame):
    """中断信号处理"""
    global _interrupted
    _interrupted = True
    print("\n⚠️  收到中断信号，将在当前任务完成后退出...")


# 注册信号处理器
signal.signal(signal.SIGINT, _signal_handler)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, _signal_handler)


def _check_interrupted():
    """检查是否被中断"""
    global _interrupted
    if _interrupted:
        raise OperationCancelledError("操作被用户中断")


def batch_copy(
    source_paths: List[str | Path],
    destination: str | Path,
    pattern: Optional[str] = None,
    overwrite: bool = False,
    preserve_metadata: bool = True,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Dict[str, Any]:
    """
    批量复制文件
    
    Args:
        source_paths: 源文件/目录路径列表
        destination: 目标目录
        pattern: 文件名模式（如 "*.py"），如果指定则只复制匹配的文件
        overwrite: 是否覆盖已存在的文件
        preserve_metadata: 是否保留文件元数据
        progress_callback: 进度回调函数 (current, total, current_file)
    
    Returns:
        操作结果字典，包含：
        - success_count: 成功数量
        - failed_count: 失败数量
        - failed_files: 失败的文件列表
        - total_count: 总数量
    """
    dest_dir = Path(destination)
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # 收集所有要复制的文件
    files_to_copy = []
    for source in source_paths:
        source_path = Path(source)
        if not source_path.exists():
            continue
        
        if source_path.is_file():
            if pattern is None or fnmatch(source_path.name, pattern):
                files_to_copy.append((source_path, dest_dir / source_path.name))
        elif source_path.is_dir():
            # 递归查找目录中的文件
            for file_path in source_path.rglob("*"):
                if file_path.is_file():
                    if pattern is None or fnmatch(file_path.name, pattern):
                        relative_path = file_path.relative_to(source_path)
                        dest_file = dest_dir / relative_path
                        files_to_copy.append((file_path, dest_file))
    
    # 执行复制
    success_count = 0
    failed_count = 0
    failed_files = []
    total_count = len(files_to_copy)
    
    for i, (source_file, dest_file) in enumerate(files_to_copy, 1):
        try:
            _check_interrupted()
            
            if progress_callback:
                progress_callback(i, total_count, str(source_file))
            
            copy_file(source_file, dest_file, overwrite=overwrite, preserve_metadata=preserve_metadata)
            success_count += 1
        except Exception as e:
            failed_count += 1
            failed_files.append({"source": str(source_file), "error": str(e)})
    
    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "failed_files": failed_files,
        "total_count": total_count,
    }


def batch_move(
    source_paths: List[str | Path],
    destination: str | Path,
    pattern: Optional[str] = None,
    overwrite: bool = False,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Dict[str, Any]:
    """
    批量移动文件
    
    Args:
        source_paths: 源文件/目录路径列表
        destination: 目标目录
        pattern: 文件名模式
        overwrite: 是否覆盖已存在的文件
        progress_callback: 进度回调函数
    
    Returns:
        操作结果字典
    """
    dest_dir = Path(destination)
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # 收集所有要移动的文件
    files_to_move = []
    for source in source_paths:
        source_path = Path(source)
        if not source_path.exists():
            continue
        
        if source_path.is_file():
            if pattern is None or fnmatch(source_path.name, pattern):
                files_to_move.append((source_path, dest_dir / source_path.name))
        elif source_path.is_dir():
            for file_path in source_path.rglob("*"):
                if file_path.is_file():
                    if pattern is None or fnmatch(file_path.name, pattern):
                        relative_path = file_path.relative_to(source_path)
                        dest_file = dest_dir / relative_path
                        files_to_move.append((file_path, dest_file))
    
    # 执行移动
    success_count = 0
    failed_count = 0
    failed_files = []
    total_count = len(files_to_move)
    
    for i, (source_file, dest_file) in enumerate(files_to_move, 1):
        try:
            _check_interrupted()
            
            if progress_callback:
                progress_callback(i, total_count, str(source_file))
            
            move_file(source_file, dest_file, overwrite=overwrite)
            success_count += 1
        except Exception as e:
            failed_count += 1
            failed_files.append({"source": str(source_file), "error": str(e)})
    
    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "failed_files": failed_files,
        "total_count": total_count,
    }


def batch_delete(
    file_paths: List[str | Path],
    pattern: Optional[str] = None,
    recursive: bool = False,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Dict[str, Any]:
    """
    批量删除文件
    
    Args:
        file_paths: 文件/目录路径列表
        pattern: 文件名模式
        recursive: 是否递归删除目录
        progress_callback: 进度回调函数
    
    Returns:
        操作结果字典
    """
    # 收集所有要删除的文件
    files_to_delete = []
    for file_path in file_paths:
        path = Path(file_path)
        if not path.exists():
            continue
        
        if path.is_file():
            if pattern is None or fnmatch(path.name, pattern):
                files_to_delete.append(path)
        elif path.is_dir() and recursive:
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    if pattern is None or fnmatch(file_path.name, pattern):
                        files_to_delete.append(file_path)
    
    # 执行删除
    success_count = 0
    failed_count = 0
    failed_files = []
    total_count = len(files_to_delete)
    
    for i, file_path in enumerate(files_to_delete, 1):
        try:
            _check_interrupted()
            
            if progress_callback:
                progress_callback(i, total_count, str(file_path))
            
            delete_file(file_path, missing_ok=True)
            success_count += 1
        except Exception as e:
            failed_count += 1
            failed_files.append({"file": str(file_path), "error": str(e)})
    
    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "failed_files": failed_files,
        "total_count": total_count,
    }


def batch_rename(
    file_paths: List[str | Path],
    rename_func: Optional[Callable[[Path], str]] = None,
    name_template: Optional[str] = None,
    pattern: Optional[str] = None,
    replacement: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Dict[str, Any]:
    """
    批量重命名文件
    
    Args:
        file_paths: 文件路径列表
        rename_func: 重命名函数，接收 Path 返回新文件名
        name_template: 名称模板（支持 {index}, {name}, {stem}, {suffix}）
        pattern: 正则表达式模式（用于替换文件名中的部分）
        replacement: 替换字符串
        progress_callback: 进度回调函数
    
    Returns:
        操作结果字典
    """
    files_to_rename = []
    for file_path in file_paths:
        path = Path(file_path)
        if path.exists() and path.is_file():
            files_to_rename.append(path)
    
    success_count = 0
    failed_count = 0
    failed_files = []
    total_count = len(files_to_rename)
    
    for i, file_path in enumerate(files_to_rename, 1):
        try:
            _check_interrupted()
            
            if progress_callback:
                progress_callback(i, total_count, str(file_path))
            
            # 确定新文件名
            if rename_func:
                new_name = rename_func(file_path)
            elif name_template:
                new_name = name_template.format(
                    index=i,
                    name=file_path.name,
                    stem=file_path.stem,
                    suffix=file_path.suffix,
                )
            elif pattern and replacement is not None:
                new_name = re.sub(pattern, replacement, file_path.name)
            else:
                raise FileOperationError("必须提供 rename_func、name_template 或 pattern/replacement")
            
            rename_file(file_path, new_name, overwrite=False)
            success_count += 1
        except Exception as e:
            failed_count += 1
            failed_files.append({"file": str(file_path), "error": str(e)})
    
    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "failed_files": failed_files,
        "total_count": total_count,
    }


def batch_replace_content(
    file_paths: List[str | Path],
    old_text: str,
    new_text: str,
    pattern: Optional[str] = None,
    regex: bool = False,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Dict[str, Any]:
    """
    批量替换文件内容
    
    Args:
        file_paths: 文件路径列表
        old_text: 要替换的文本或正则表达式
        new_text: 替换后的文本
        pattern: 文件名模式（只处理匹配的文件）
        regex: 是否使用正则表达式
        progress_callback: 进度回调函数
    
    Returns:
        操作结果字典
    """
    files_to_process = []
    for file_path in file_paths:
        path = Path(file_path)
        if path.exists() and path.is_file():
            if pattern is None or fnmatch(path.name, pattern):
                files_to_process.append(path)
    
    success_count = 0
    failed_count = 0
    failed_files = []
    total_count = len(files_to_process)
    total_replacements = 0
    
    for i, file_path in enumerate(files_to_process, 1):
        try:
            _check_interrupted()
            
            if progress_callback:
                progress_callback(i, total_count, str(file_path))
            
            count = replace_content(file_path, old_text, new_text, regex=regex)
            total_replacements += count
            success_count += 1
        except Exception as e:
            failed_count += 1
            failed_files.append({"file": str(file_path), "error": str(e)})
    
    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "failed_files": failed_files,
        "total_count": total_count,
        "total_replacements": total_replacements,
    }

