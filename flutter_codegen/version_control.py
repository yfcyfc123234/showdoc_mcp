"""
版本控制管理器（Flutter 版本）

复用 android_codegen 的版本控制逻辑
"""
import sys
from pathlib import Path

# 导入 android_codegen 的版本控制管理器
sys.path.insert(0, str(Path(__file__).parent.parent))
from android_codegen.version_control import VersionControlManager

# 直接导出，但修改缓存目录名称
class FlutterVersionControlManager(VersionControlManager):
    """Flutter 版本控制管理器"""
    
    def __init__(self, output_dir: Path):
        """
        初始化版本控制管理器
        
        Args:
            output_dir: 输出目录
        """
        super().__init__(output_dir)
        # 修改缓存目录名称
        self.cache_dir = self.output_dir / ".flutter_codegen_cache"
        self.index_file = self.cache_dir / "file_index.json"
        
        # 重新创建缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 重新加载索引（使用新的索引文件路径）
        self.file_index = self._load_index()


__all__ = ["FlutterVersionControlManager"]

