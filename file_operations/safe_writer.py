"""
智能文件写入器

提供安全、原子的文件写入功能，支持备份、权限保留等。
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Literal
from contextlib import contextmanager

from .exceptions import FileOperationError, BackupError


class SafeFileWriter:
    """
    安全文件写入器
    
    特性：
    - 原子写入：先写临时文件，再替换，避免写入中断导致文件损坏
    - 自动备份：写入前自动备份原文件
    - 权限保留：保留原文件的权限和元数据
    - 自动创建目录：自动创建不存在的目录
    """
    
    def __init__(
        self,
        file_path: str | Path,
        encoding: str = "utf-8",
        backup: bool = True,
        preserve_permissions: bool = True,
    ):
        """
        初始化安全文件写入器
        
        Args:
            file_path: 文件路径
            encoding: 文件编码
            backup: 是否在写入前备份原文件
            preserve_permissions: 是否保留原文件权限
        """
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.backup = backup
        self.preserve_permissions = preserve_permissions
        self.backup_path: Optional[Path] = None
        self.temp_path: Optional[Path] = None
        self._original_stat: Optional[os.stat_result] = None
    
    def _create_backup(self) -> Path:
        """创建备份文件"""
        if not self.file_path.exists():
            raise BackupError("无法备份不存在的文件")
        
        timestamp = self.file_path.stat().st_mtime
        backup_path = self.file_path.parent / f"{self.file_path.name}.backup.{int(timestamp)}"
        
        try:
            shutil.copy2(self.file_path, backup_path)
            return backup_path
        except Exception as e:
            raise BackupError(f"创建备份失败: {e}")
    
    def _get_temp_path(self) -> Path:
        """获取临时文件路径"""
        temp_dir = self.file_path.parent
        temp_name = f".{self.file_path.name}.tmp"
        return temp_dir / temp_name
    
    def _preserve_metadata(self, source: Path, target: Path):
        """保留文件元数据"""
        if not source.exists():
            return
        
        try:
            stat_info = source.stat()
            # 保留权限
            if self.preserve_permissions:
                target.chmod(stat_info.st_mode)
            # 保留时间戳
            os.utime(target, (stat_info.st_atime, stat_info.st_mtime))
        except Exception:
            # 如果保留元数据失败，不影响主流程
            pass
    
    def write(self, content: str, mode: Literal["write", "append"] = "write"):
        """
        写入内容
        
        Args:
            content: 要写入的内容
            mode: 写入模式，"write" 覆盖写入，"append" 追加写入
        
        Raises:
            FileOperationError: 写入失败
        """
        # 确保目录存在
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存原文件信息
        if self.file_path.exists():
            self._original_stat = self.file_path.stat()
            
            # 创建备份
            if self.backup:
                self.backup_path = self._create_backup()
        
        # 获取临时文件路径
        self.temp_path = self._get_temp_path()
        
        try:
            # 写入临时文件
            if mode == "append" and self.file_path.exists():
                # 追加模式：先读取原内容
                original_content = self.file_path.read_text(encoding=self.encoding)
                self.temp_path.write_text(original_content + content, encoding=self.encoding)
            else:
                # 覆盖模式
                self.temp_path.write_text(content, encoding=self.encoding)
            
            # 保留元数据
            if self._original_stat:
                self._preserve_metadata(self.file_path, self.temp_path)
            
            # 原子替换
            if self.file_path.exists():
                self.file_path.unlink()
            self.temp_path.rename(self.file_path)
            self.temp_path = None
            
        except Exception as e:
            # 清理临时文件
            if self.temp_path and self.temp_path.exists():
                try:
                    self.temp_path.unlink()
                except Exception:
                    pass
            raise FileOperationError(f"写入文件失败: {e}")
    
    def insert(self, content: str, position: int):
        """
        在指定位置插入内容
        
        Args:
            content: 要插入的内容
            position: 插入位置（字符位置）
        
        Raises:
            FileOperationError: 插入失败
        """
        if not self.file_path.exists():
            raise FileOperationError(f"文件不存在: {self.file_path}")
        
        # 读取原内容
        original_content = self.file_path.read_text(encoding=self.encoding)
        
        # 插入内容
        new_content = original_content[:position] + content + original_content[position:]
        
        # 写入
        self.write(new_content, mode="write")
    
    def insert_lines(self, content: str, line_number: int):
        """
        在指定行号插入内容
        
        Args:
            content: 要插入的内容
            line_number: 行号（从1开始）
        
        Raises:
            FileOperationError: 插入失败
        """
        if not self.file_path.exists():
            raise FileOperationError(f"文件不存在: {self.file_path}")
        
        # 读取原内容
        lines = self.file_path.read_text(encoding=self.encoding).splitlines(keepends=True)
        
        # 插入内容
        if line_number < 1:
            line_number = 1
        if line_number > len(lines):
            # 追加到末尾
            lines.append(content + "\n" if not content.endswith("\n") else content)
        else:
            lines.insert(line_number - 1, content + "\n" if not content.endswith("\n") else content)
        
        # 写入
        new_content = "".join(lines)
        self.write(new_content, mode="write")
    
    def cleanup_backup(self):
        """清理备份文件"""
        if self.backup_path and self.backup_path.exists():
            try:
                self.backup_path.unlink()
            except Exception:
                pass
    
    def restore_from_backup(self):
        """从备份恢复文件"""
        if not self.backup_path or not self.backup_path.exists():
            raise BackupError("备份文件不存在")
        
        try:
            shutil.copy2(self.backup_path, self.file_path)
            if self._original_stat:
                self._preserve_metadata(self.backup_path, self.file_path)
        except Exception as e:
            raise BackupError(f"恢复备份失败: {e}")
    
    @contextmanager
    def atomic_write(self, mode: Literal["write", "append"] = "write"):
        """
        原子写入上下文管理器
        
        使用示例：
            with writer.atomic_write() as f:
                f.write("content")
        """
        temp_file = None
        try:
            # 确保目录存在
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建备份
            if self.backup and self.file_path.exists():
                self.backup_path = self._create_backup()
                self._original_stat = self.file_path.stat()
            
            # 创建临时文件
            self.temp_path = self._get_temp_path()
            temp_file = open(self.temp_path, "w", encoding=self.encoding)
            
            # 如果是追加模式，先写入原内容
            if mode == "append" and self.file_path.exists():
                original_content = self.file_path.read_text(encoding=self.encoding)
                temp_file.write(original_content)
            
            yield temp_file
            
            temp_file.close()
            temp_file = None
            
            # 保留元数据
            if self._original_stat:
                self._preserve_metadata(self.file_path, self.temp_path)
            
            # 原子替换
            if self.file_path.exists():
                self.file_path.unlink()
            self.temp_path.rename(self.file_path)
            self.temp_path = None
            
        except Exception as e:
            if temp_file:
                try:
                    temp_file.close()
                except Exception:
                    pass
            if self.temp_path and self.temp_path.exists():
                try:
                    self.temp_path.unlink()
                except Exception:
                    pass
            raise FileOperationError(f"原子写入失败: {e}")

