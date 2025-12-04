"""
文件备份和恢复工具

提供文件自动备份、带时间戳的备份、备份管理等功能。
"""

import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .exceptions import FileOperationError, BackupError
from .file_utils import get_file_info


def backup_file(
    file_path: str | Path,
    backup_dir: Optional[str | Path] = None,
    suffix: str = ".backup",
    timestamp_format: str = "%Y%m%d_%H%M%S",
) -> Path:
    """
    备份文件
    
    Args:
        file_path: 要备份的文件路径
        backup_dir: 备份目录（如果为 None 则在原文件同目录）
        suffix: 备份文件后缀
        timestamp_format: 时间戳格式
    
    Returns:
        备份文件路径
    
    Raises:
        FileNotFoundError: 文件不存在
        BackupError: 备份失败
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    if not path.is_file():
        raise FileOperationError(f"路径不是文件: {path}")
    
    # 确定备份目录
    if backup_dir:
        backup_dir_path = Path(backup_dir)
        backup_dir_path.mkdir(parents=True, exist_ok=True)
    else:
        backup_dir_path = path.parent
    
    # 生成备份文件名
    timestamp = datetime.now().strftime(timestamp_format)
    backup_name = f"{path.stem}_{timestamp}{suffix}{path.suffix}"
    backup_path = backup_dir_path / backup_name
    
    try:
        shutil.copy2(path, backup_path)
        return backup_path
    except Exception as e:
        raise BackupError(f"备份文件失败: {e}")


def restore_file(
    backup_path: str | Path,
    target_path: Optional[str | Path] = None,
    overwrite: bool = False,
) -> Path:
    """
    从备份恢复文件
    
    Args:
        backup_path: 备份文件路径
        target_path: 目标文件路径（如果为 None 则从备份文件名推断）
        overwrite: 是否覆盖已存在的文件
    
    Returns:
        恢复后的文件路径
    
    Raises:
        FileNotFoundError: 备份文件不存在
        BackupError: 恢复失败
    """
    backup = Path(backup_path)
    
    if not backup.exists():
        raise FileNotFoundError(f"备份文件不存在: {backup}")
    
    # 确定目标路径
    if target_path:
        target = Path(target_path)
    else:
        # 从备份文件名推断（移除时间戳和后缀）
        # 例如: file_20240101_120000.backup.txt -> file.txt
        name = backup.stem
        # 移除 .backup 后缀
        if name.endswith(".backup"):
            name = name[:-7]
        # 移除时间戳（格式: _YYYYMMDD_HHMMSS）
        parts = name.rsplit("_", 2)
        if len(parts) >= 3:
            # 检查最后两部分是否是时间戳格式
            try:
                datetime.strptime(f"{parts[-2]}_{parts[-1]}", "%Y%m%d_%H%M%S")
                name = "_".join(parts[:-2])
            except ValueError:
                pass
        
        target = backup.parent / f"{name}{backup.suffix}"
    
    if target.exists() and not overwrite:
        raise FileOperationError(f"目标文件已存在: {target}")
    
    try:
        shutil.copy2(backup, target)
        return target
    except Exception as e:
        raise BackupError(f"恢复文件失败: {e}")


def list_backups(
    file_path: str | Path,
    backup_dir: Optional[str | Path] = None,
    suffix: str = ".backup",
) -> List[Dict[str, Any]]:
    """
    列出文件的所有备份
    
    Args:
        file_path: 原文件路径
        backup_dir: 备份目录（如果为 None 则在原文件同目录）
        suffix: 备份文件后缀
    
    Returns:
        备份文件信息列表，每个备份包含：
        - path: 备份文件路径
        - created_time: 创建时间
        - size: 文件大小
    """
    path = Path(file_path)
    
    # 确定备份目录
    if backup_dir:
        backup_dir_path = Path(backup_dir)
    else:
        backup_dir_path = path.parent
    
    if not backup_dir_path.exists():
        return []
    
    backups = []
    base_name = path.stem
    
    # 查找所有匹配的备份文件
    for backup_file in backup_dir_path.glob(f"{base_name}_*{suffix}{path.suffix}"):
        try:
            info = get_file_info(backup_file)
            backups.append({
                "path": str(backup_file),
                "created_time": info.get("created_time"),
                "size": info["size"],
            })
        except Exception:
            continue
    
    # 按创建时间排序（最新的在前）
    backups.sort(key=lambda x: x.get("created_time", ""), reverse=True)
    
    return backups


def cleanup_old_backups(
    file_path: str | Path,
    backup_dir: Optional[str | Path] = None,
    suffix: str = ".backup",
    keep_count: int = 5,
) -> int:
    """
    清理旧的备份文件，只保留最新的几个
    
    Args:
        file_path: 原文件路径
        backup_dir: 备份目录
        suffix: 备份文件后缀
        keep_count: 保留的备份数量
    
    Returns:
        删除的备份文件数量
    """
    backups = list_backups(file_path, backup_dir=backup_dir, suffix=suffix)
    
    if len(backups) <= keep_count:
        return 0
    
    # 删除多余的备份
    deleted_count = 0
    for backup in backups[keep_count:]:
        try:
            Path(backup["path"]).unlink()
            deleted_count += 1
        except Exception:
            pass
    
    return deleted_count

