"""
MCP 集成入口包：ShowDoc 抓取 + Android 代码生成

本包仅做「薄封装」：
- 复用 `core.ShowDocClient` 完成 ShowDoc 接口树抓取；
- 复用 `android_codegen.AndroidCodeGenerator` 完成 Android 代码生成；
- 通过 MCP 协议把这两个能力（加一个打开输出目录的小工具）暴露给上层。
"""

from .server import (
    showdoc_fetch_apis,
    android_generate_from_showdoc,
    android_open_output_folder,
    showdoc_fetch_and_generate,
)

__all__ = [
    "showdoc_fetch_apis",
    "android_generate_from_showdoc",
    "android_open_output_folder",
    "showdoc_fetch_and_generate",
]


