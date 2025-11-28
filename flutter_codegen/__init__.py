"""
Flutter 代码生成器模块

从 ShowDoc 自动生成 Flutter/Dart 代码，包括：
- Dio Service 接口
- Dart 实体类（使用 json_serializable）
- Repository 层
- Dio 配置
"""

from .generator import FlutterCodeGenerator

__all__ = ["FlutterCodeGenerator"]

