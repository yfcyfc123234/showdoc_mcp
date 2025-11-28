"""
Flutter 代码生成工具函数

复用 android_codegen 的工具函数，但适配 Dart 命名规范
"""
import sys
from pathlib import Path

# 导入 android_codegen 的工具函数
sys.path.insert(0, str(Path(__file__).parent.parent))
from android_codegen.utils import (
    translate_chinese_to_english,
    to_pascal_case,
    to_camel_case,
    extract_name_from_url,
    url_path_to_method_name,
    url_path_to_class_name,
)

# Dart 关键字列表
DART_KEYWORDS = {
    "abstract", "as", "assert", "async", "await", "break", "case", "catch",
    "class", "const", "continue", "covariant", "default", "deferred", "do",
    "dynamic", "else", "enum", "export", "extends", "extension", "external",
    "factory", "false", "final", "finally", "for", "Function", "get", "hide",
    "if", "implements", "import", "in", "interface", "is", "late", "library",
    "mixin", "new", "null", "on", "operator", "part", "required", "rethrow",
    "return", "set", "show", "static", "super", "switch", "sync", "this",
    "throw", "true", "try", "typedef", "var", "void", "while", "with", "yield"
}


def sanitize_class_name(name: str) -> str:
    """清理类名，确保符合 Dart 规范"""
    # 转换为帕斯卡命名
    name = to_pascal_case(name)
    
    if name.lower() in DART_KEYWORDS:
        name = name + "Type"
    
    # 确保以字母开头
    if name and not name[0].isalpha():
        name = "A" + name
    
    return name


def sanitize_method_name(name: str) -> str:
    """清理方法名，确保符合 Dart 规范"""
    name = to_camel_case(name)
    
    if name.lower() in DART_KEYWORDS:
        name = name + "Method"
    
    # 确保以字母开头
    if name and not name[0].isalpha():
        name = "a" + name
    
    return name


def sanitize_field_name(name: str) -> str:
    """清理字段名，确保符合 Dart 规范"""
    # 转换为驼峰命名
    name = to_camel_case(name)
    
    if name.lower() in DART_KEYWORDS:
        name = name + "Field"
    
    # 确保以字母开头
    if name and not name[0].isalpha():
        name = "a" + name
    
    return name


__all__ = [
    "translate_chinese_to_english",
    "to_pascal_case",
    "to_camel_case",
    "extract_name_from_url",
    "url_path_to_method_name",
    "url_path_to_class_name",
    "sanitize_class_name",
    "sanitize_method_name",
    "sanitize_field_name",
    "DART_KEYWORDS",
]

