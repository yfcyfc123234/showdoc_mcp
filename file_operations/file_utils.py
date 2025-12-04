"""
基础文件操作工具
"""

import os
import shutil
import stat
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .exceptions import (
    FileOperationError,
    InvalidPathError,
)
# FileNotFoundError 和 PermissionError 是 Python 内置异常，直接使用


def copy_file(
    source: str | Path,
    destination: str | Path,
    overwrite: bool = False,
    preserve_metadata: bool = True,
) -> Path:
    """
    复制文件
    
    Args:
        source: 源文件路径
        destination: 目标文件路径
        overwrite: 是否覆盖已存在的文件
        preserve_metadata: 是否保留文件元数据（时间戳、权限等）
    
    Returns:
        目标文件路径
    
    Raises:
        FileNotFoundError: 源文件不存在
        FileOperationError: 目标文件已存在且 overwrite=False
        PermissionError: 权限不足
    """
    source_path = Path(source)
    dest_path = Path(destination)
    
    if not source_path.exists():
        raise FileNotFoundError(f"源文件不存在: {source_path}")
    
    if not source_path.is_file():
        raise FileOperationError(f"源路径不是文件: {source_path}")
    
    if dest_path.exists() and not overwrite:
        raise FileOperationError(f"目标文件已存在: {dest_path}")
    
    # 确保目标目录存在
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if preserve_metadata:
            shutil.copy2(source_path, dest_path)
        else:
            shutil.copy(source_path, dest_path)
        return dest_path
    except PermissionError as e:
        raise PermissionError(f"权限不足，无法复制文件: {e}")
    except Exception as e:
        raise FileOperationError(f"复制文件失败: {e}")


def move_file(
    source: str | Path,
    destination: str | Path,
    overwrite: bool = False,
) -> Path:
    """
    移动文件
    
    Args:
        source: 源文件路径
        destination: 目标文件路径
        overwrite: 是否覆盖已存在的文件
    
    Returns:
        目标文件路径
    
    Raises:
        FileNotFoundError: 源文件不存在
        FileOperationError: 目标文件已存在且 overwrite=False
        PermissionError: 权限不足
    """
    source_path = Path(source)
    dest_path = Path(destination)
    
    if not source_path.exists():
        raise FileNotFoundError(f"源文件不存在: {source_path}")
    
    if not source_path.is_file():
        raise FileOperationError(f"源路径不是文件: {source_path}")
    
    if dest_path.exists() and not overwrite:
        raise FileOperationError(f"目标文件已存在: {dest_path}")
    
    # 确保目标目录存在
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        shutil.move(str(source_path), str(dest_path))
        return dest_path
    except PermissionError as e:
        raise PermissionError(f"权限不足，无法移动文件: {e}")
    except Exception as e:
        raise FileOperationError(f"移动文件失败: {e}")


def delete_file(
    file_path: str | Path,
    missing_ok: bool = True,
) -> bool:
    """
    删除文件
    
    Args:
        file_path: 文件路径
        missing_ok: 如果文件不存在是否忽略错误
    
    Returns:
        是否成功删除
    
    Raises:
        FileOperationError: 路径不是文件
        PermissionError: 权限不足
    """
    path = Path(file_path)
    
    if not path.exists():
        if missing_ok:
            return False
        raise FileNotFoundError(f"文件不存在: {path}")
    
    if not path.is_file():
        raise FileOperationError(f"路径不是文件: {path}")
    
    try:
        path.unlink()
        return True
    except PermissionError as e:
        raise PermissionError(f"权限不足，无法删除文件: {e}")
    except Exception as e:
        raise FileOperationError(f"删除文件失败: {e}")


def create_file(
    file_path: str | Path,
    content: str = "",
    encoding: str = "utf-8",
    overwrite: bool = False,
) -> Path:
    """
    创建文件
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 文件编码
        overwrite: 是否覆盖已存在的文件
    
    Returns:
        创建的文件路径
    
    Raises:
        FileOperationError: 文件已存在且 overwrite=False
        PermissionError: 权限不足
    """
    path = Path(file_path)
    
    if path.exists() and not overwrite:
        raise FileOperationError(f"文件已存在: {path}")
    
    # 确保目录存在
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        path.write_text(content, encoding=encoding)
        return path
    except PermissionError as e:
        raise PermissionError(f"权限不足，无法创建文件: {e}")
    except Exception as e:
        raise FileOperationError(f"创建文件失败: {e}")


def create_directory(
    dir_path: str | Path,
    parents: bool = True,
    exist_ok: bool = True,
) -> Path:
    """
    创建目录
    
    Args:
        dir_path: 目录路径
        parents: 是否创建父目录
        exist_ok: 如果目录已存在是否忽略错误
    
    Returns:
        创建的目录路径
    
    Raises:
        FileOperationError: 路径已存在但不是目录
        PermissionError: 权限不足
    """
    path = Path(dir_path)
    
    try:
        path.mkdir(parents=parents, exist_ok=exist_ok)
        return path
    except FileExistsError:
        if not exist_ok:
            raise FileOperationError(f"目录已存在: {path}")
        return path
    except PermissionError as e:
        raise PermissionError(f"权限不足，无法创建目录: {e}")
    except Exception as e:
        raise FileOperationError(f"创建目录失败: {e}")


def rename_file(
    file_path: str | Path,
    new_name: str,
    overwrite: bool = False,
) -> Path:
    """
    重命名文件
    
    Args:
        file_path: 文件路径
        new_name: 新文件名
        overwrite: 是否覆盖已存在的文件
    
    Returns:
        重命名后的文件路径
    
    Raises:
        FileNotFoundError: 文件不存在
        FileOperationError: 目标文件已存在且 overwrite=False
        PermissionError: 权限不足
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    new_path = path.parent / new_name
    
    if new_path.exists() and not overwrite:
        raise FileOperationError(f"目标文件已存在: {new_path}")
    
    try:
        path.rename(new_path)
        return new_path
    except PermissionError as e:
        raise PermissionError(f"权限不足，无法重命名文件: {e}")
    except Exception as e:
        raise FileOperationError(f"重命名文件失败: {e}")


def file_exists(file_path: str | Path) -> bool:
    """
    检查文件是否存在
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件是否存在
    """
    return Path(file_path).exists()


def get_file_info(file_path: str | Path) -> Dict[str, Any]:
    """
    获取文件信息
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件信息字典，包含：
        - path: 文件路径
        - exists: 是否存在
        - is_file: 是否是文件
        - is_dir: 是否是目录
        - size: 文件大小（字节）
        - modified_time: 修改时间
        - created_time: 创建时间（如果支持）
        - permissions: 权限信息
    
    Raises:
        FileNotFoundError: 文件不存在
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    stat_info = path.stat()
    
    info = {
        "path": str(path.resolve()),
        "exists": True,
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
        "size": stat_info.st_size,
        "modified_time": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
        "permissions": oct(stat_info.st_mode)[-3:],
    }
    
    # 尝试获取创建时间（Windows 支持，Unix 可能不支持）
    try:
        info["created_time"] = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
    except (AttributeError, OSError):
        info["created_time"] = None
    
    return info


def set_file_permissions(
    file_path: str | Path,
    mode: int,
) -> bool:
    """
    设置文件权限（Unix/Linux/Mac）
    
    Args:
        file_path: 文件路径
        mode: 权限模式（八进制，如 0o755）
    
    Returns:
        是否成功
    
    Raises:
        FileNotFoundError: 文件不存在
        PermissionError: 权限不足
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    try:
        path.chmod(mode)
        return True
    except PermissionError as e:
        raise PermissionError(f"权限不足，无法设置文件权限: {e}")
    except Exception as e:
        raise FileOperationError(f"设置文件权限失败: {e}")

