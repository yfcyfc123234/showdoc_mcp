"""
Android 代码生成器模块

将 core 模块返回的 API 数据转换为 Android 可用的代码，包括：
- Retrofit2 Service 接口
- Android 实体类（Data Class）
- OkHttp 配置示例
"""

from .generator import AndroidCodeGenerator
from .retrofit_generator import RetrofitServiceGenerator
from .entity_generator import AndroidEntityGenerator
from .okhttp_config import OkHttpConfigGenerator
from . import utils

__all__ = [
    'AndroidCodeGenerator',
    'RetrofitServiceGenerator',
    'AndroidEntityGenerator',
    'OkHttpConfigGenerator',
    'utils',
]

