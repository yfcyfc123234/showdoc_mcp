"""
临时文件管理工具

提供临时文件和目录的创建、管理、自动清理功能。
"""

import tempfile
import atexit
import shutil
from pathlib import Path
from typing import Optional, List
from contextlib import contextmanager

from .exceptions import FileOperationError
from .file_utils import create_file, create_directory


# 全局临时文件/目录列表，用于自动清理
_temp_resources: List[Path] = []


def _cleanup_temp_resources():
    """清理所有临时资源"""
    for resource in _temp_resources:
        try:
            if resource.is_file():
                resource.unlink()
            elif resource.is_dir():
                shutil.rmtree(resource)
        except Exception:
            pass
    _temp_resources.clear()


# 注册退出时清理
atexit.register(_cleanup_temp_resources)


def create_temp_file(
    suffix: Optional[str] = None,
    prefix: Optional[str] = None,
    dir: Optional[str | Path] = None,
    content: str = "",
    delete_on_exit: bool = True,
) -> Path:
    """
    创建临时文件
    
    Args:
        suffix: 文件后缀（如 ".txt"）
        prefix: 文件前缀
        dir: 临时文件目录（如果为 None 则使用系统临时目录）
        content: 文件初始内容
        delete_on_exit: 是否在程序退出时自动删除
    
    Returns:
        临时文件路径
    """
    if dir:
        dir_path = Path(dir)
        dir_path.mkdir(parents=True, exist_ok=True)
    else:
        dir_path = None
    
    fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=str(dir_path) if dir_path else None)
    
    try:
        temp_file = Path(temp_path)
        
        if content:
            temp_file.write_text(content, encoding="utf-8")
        
        if delete_on_exit:
            _temp_resources.append(temp_file)
        
        return temp_file
    finally:
        import os
        os.close(fd)


def create_temp_directory(
    suffix: Optional[str] = None,
    prefix: Optional[str] = None,
    dir: Optional[str | Path] = None,
    delete_on_exit: bool = True,
) -> Path:
    """
    创建临时目录
    
    Args:
        suffix: 目录后缀
        prefix: 目录前缀
        dir: 临时目录的父目录（如果为 None 则使用系统临时目录）
        delete_on_exit: 是否在程序退出时自动删除
    
    Returns:
        临时目录路径
    """
    if dir:
        dir_path = Path(dir)
        dir_path.mkdir(parents=True, exist_ok=True)
    else:
        dir_path = None
    
    temp_dir = Path(tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=str(dir_path) if dir_path else None))
    
    if delete_on_exit:
        _temp_resources.append(temp_dir)
    
    return temp_dir


@contextmanager
def temp_file_context(
    suffix: Optional[str] = None,
    prefix: Optional[str] = None,
    dir: Optional[str | Path] = None,
    content: str = "",
):
    """
    临时文件上下文管理器
    
    使用示例：
        with temp_file_context(suffix=".txt") as temp_file:
            temp_file.write_text("content")
    """
    temp_file = create_temp_file(suffix=suffix, prefix=prefix, dir=dir, content=content, delete_on_exit=True)
    try:
        yield temp_file
    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass


@contextmanager
def temp_directory_context(
    suffix: Optional[str] = None,
    prefix: Optional[str] = None,
    dir: Optional[str | Path] = None,
):
    """
    临时目录上下文管理器
    
    使用示例：
        with temp_directory_context() as temp_dir:
            (temp_dir / "file.txt").write_text("content")
    """
    temp_dir = create_temp_directory(suffix=suffix, prefix=prefix, dir=dir, delete_on_exit=True)
    try:
        yield temp_dir
    finally:
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass


def cleanup_temp_resource(resource_path: str | Path):
    """
    手动清理临时资源
    
    Args:
        resource_path: 临时资源路径
    """
    path = Path(resource_path)
    
    if path in _temp_resources:
        _temp_resources.remove(path)
    
    try:
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
    except Exception as e:
        raise FileOperationError(f"清理临时资源失败: {e}")

