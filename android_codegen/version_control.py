"""
版本控制管理器

用于管理生成文件的版本，支持增量更新和删除检测
"""
import hashlib
import json
from pathlib import Path
from typing import Dict, Set, Optional, List, Tuple
from datetime import datetime


class VersionControlManager:
    """版本控制管理器"""
    
    def __init__(self, output_dir: Path):
        """
        初始化版本控制管理器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.cache_dir = self.output_dir / ".android_codegen_cache"
        self.index_file = self.cache_dir / "file_index.json"
        
        # 创建缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载现有的文件索引
        self.file_index = self._load_index()
    
    def _load_index(self) -> Dict[str, Dict[str, any]]:
        """加载文件索引"""
        if not self.index_file.exists():
            return {}
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_index(self):
        """保存文件索引"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[警告] 保存文件索引失败: {e}")
    
    def _calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """计算文件哈希值"""
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception:
            return None
    
    def _calculate_content_hash(self, content: str) -> str:
        """计算内容哈希值"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get_file_info(self, relative_path: str) -> Optional[Dict[str, any]]:
        """
        获取文件的版本信息
        
        Args:
            relative_path: 相对于输出目录的文件路径
        
        Returns:
            文件信息字典，包含 hash、mtime 等，如果文件不存在则返回 None
        """
        return self.file_index.get(relative_path)
    
    def record_file(self, relative_path: str, content_hash: str, api_key: Optional[Tuple[str, str]] = None):
        """
        记录生成的文件
        
        Args:
            relative_path: 相对于输出目录的文件路径
            content_hash: 文件内容的哈希值
            api_key: 关联的 API 键 (url, method)，用于删除检测
        """
        full_path = self.output_dir / relative_path
        mtime = datetime.now().isoformat() if full_path.exists() else None
        
        self.file_index[relative_path] = {
            "hash": content_hash,
            "mtime": mtime,
            "api_key": list(api_key) if api_key else None
        }
    
    def compare_files(
        self, 
        new_files: Dict[str, str]
    ) -> Tuple[Dict[str, str], Set[str], Set[str]]:
        """
        比较新旧文件列表
        
        Args:
            new_files: 新文件字典 {relative_path: content_hash}
        
        Returns:
            (需要更新的文件, 需要删除的文件, 保持不变的文件)
        """
        new_paths = set(new_files.keys())
        old_paths = set(self.file_index.keys())
        
        # 需要更新的文件（新增或内容有变化）
        to_update = {}
        for path, new_hash in new_files.items():
            old_info = self.file_index.get(path)
            if not old_info or old_info.get("hash") != new_hash:
                to_update[path] = new_hash
        
        # 需要删除的文件（旧文件不在新列表中）
        to_delete = old_paths - new_paths
        
        # 保持不变的文件
        unchanged = new_paths - set(to_update.keys())
        
        return to_update, to_delete, unchanged
    
    def get_orphaned_api_files(self, api_keys: Set[Tuple[str, str]]) -> List[str]:
        """
        获取孤立的 API 相关文件（API 已不存在但文件还在）
        
        Args:
            api_keys: 当前所有 API 的键集合
        
        Returns:
            孤立的文件路径列表
        """
        orphaned = []
        api_keys_list = [list(key) for key in api_keys]
        
        for file_path, file_info in self.file_index.items():
            api_key = file_info.get("api_key")
            # 如果是 API 相关文件，且对应的 API 已不存在
            if api_key and api_key not in api_keys_list:
                orphaned.append(file_path)
        
        return orphaned
    
    def remove_file(self, relative_path: str):
        """从索引中移除文件记录"""
        if relative_path in self.file_index:
            del self.file_index[relative_path]
    
    def commit(self):
        """提交更改（保存索引）"""
        self._save_index()
    
    def clean_orphaned_files(self, orphaned_files: List[str], delete_files: bool = False):
        """
        清理孤立的文件
        
        Args:
            orphaned_files: 孤立的文件路径列表
            delete_files: 是否同时删除文件本身
        """
        for file_path in orphaned_files:
            self.remove_file(file_path)
            if delete_files:
                full_path = self.output_dir / file_path
                try:
                    if full_path.exists():
                        full_path.unlink()
                        # 尝试删除空目录
                        parent = full_path.parent
                        try:
                            if not any(parent.iterdir()):
                                parent.rmdir()
                        except:
                            pass
                except Exception as e:
                    print(f"[警告] 删除文件失败 {file_path}: {e}")
    
    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        total = len(self.file_index)
        return {
            "total_files": total,
            "indexed_files": total
        }
