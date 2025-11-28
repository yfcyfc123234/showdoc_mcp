"""
实体类 Schema 分析工具（Flutter 版本）

从 responseOriginal.data 中提取并分析实体类结构，生成嵌套实体类
适配 Dart 类型系统
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# 导入 android_codegen 的实体类 schema 分析函数
sys.path.insert(0, str(Path(__file__).parent.parent))
from android_codegen.entity_schema import (
    extract_data_from_response,
    extract_data_from_request,
    build_request_schema_from_params,
    sanitize_category_name,
)


def analyze_entity_schema(data: Any, base_name: str = "Item") -> Dict[str, Any]:
    """
    分析数据并生成实体类 Schema（支持嵌套对象，适配 Dart 类型）
    
    Args:
        data: 要分析的数据（可能是 dict、list、基本类型等）
        base_name: 基础类名（用于生成嵌套类名）
    
    Returns:
        {
            "schema": {...},  # 当前实体的 schema
            "nested": {...}   # 嵌套的实体类定义
        }
    """
    nested_entities = {}
    
    def analyze_value(value: Any, field_name: str = "") -> Dict[str, Any]:
        """分析值并返回类型信息（Dart 类型）"""
        if value is None:
            return {"type": "dynamic", "nullable": True, "nested": None}
        
        if isinstance(value, bool):
            return {"type": "bool", "nullable": False, "nested": None}
        elif isinstance(value, int):
            return {"type": "int", "nullable": False, "nested": None}
        elif isinstance(value, float):
            return {"type": "double", "nullable": False, "nested": None}
        elif isinstance(value, str):
            return {"type": "String", "nullable": False, "nested": None}
        elif isinstance(value, list):
            if value:
                # 分析列表元素的类型
                first_item = value[0]
                item_info = analyze_value(first_item, field_name)
                
                item_type = item_info["type"]
                nested_entity = item_info.get("nested")
                
                if nested_entity:
                    # 列表元素是嵌套对象
                    nested_name = nested_entity["name"]
                    nested_entities[nested_name] = nested_entity["schema"]
                    return {
                        "type": f"List<{nested_name}>",
                        "nullable": False,
                        "nested": nested_entity
                    }
                else:
                    return {
                        "type": f"List<{item_type}>",
                        "nullable": False,
                        "nested": None
                    }
            else:
                return {"type": "List<dynamic>", "nullable": False, "nested": None}
        elif isinstance(value, dict):
            # 这是一个嵌套对象，需要生成单独的实体类
            nested_name = generate_nested_entity_name(field_name, base_name)
            
            nested_schema = {}
            nested_nested = {}
            
            for key, val in value.items():
                field_info = analyze_value(val, key)
                nested_schema[key] = {
                    "type": field_info["type"],
                    "nullable": field_info["nullable"]
                }
                
                # 如果有嵌套对象，也要收集
                if field_info.get("nested"):
                    nested_nested[field_info["nested"]["name"]] = field_info["nested"]["schema"]
            
            # 合并嵌套的实体类
            nested_entities.update(nested_nested)
            nested_entities[nested_name] = nested_schema
            
            return {
                "type": nested_name,
                "nullable": False,
                "nested": {"name": nested_name, "schema": nested_schema}
            }
        else:
            return {"type": "dynamic", "nullable": False, "nested": None}
    
    # 分析主数据结构
    if isinstance(data, dict):
        schema = {}
        for key, value in data.items():
            field_info = analyze_value(value, key)
            schema[key] = {
                "type": field_info["type"],
                "nullable": field_info["nullable"]
            }
            
            # 如果有嵌套对象，也要收集
            if field_info.get("nested"):
                nested_info = field_info["nested"]
                nested_entities[nested_info["name"]] = nested_info["schema"]
        
        return {"schema": schema, "nested": nested_entities}
    elif isinstance(data, list) and data:
        # 如果是列表，分析列表元素的类型
        first_item = data[0]
        if isinstance(first_item, dict):
            # 列表元素是对象，生成实体类
            item_schema = analyze_entity_schema(first_item, base_name)
            return item_schema
        else:
            # 列表元素是基本类型
            return {
                "schema": {},
                "nested": {}
            }
    else:
        return {"schema": {}, "nested": {}}


def generate_nested_entity_name(field_name: str, base_name: str) -> str:
    """
    生成嵌套实体类名称
    
    Args:
        field_name: 字段名
        base_name: 基础类名
    
    Returns:
        嵌套实体类名称
    """
    from .utils import sanitize_class_name
    
    # 移除 base_name 的后缀（如果存在）
    clean_base_name = base_name
    if clean_base_name.endswith("Bean"):
        clean_base_name = clean_base_name[:-4]
    
    if field_name:
        # 使用字段名生成类名
        class_name = sanitize_class_name(field_name)
        return class_name
    else:
        # 使用基础类名 + Item
        return f"{clean_base_name}Item"


def _map_showdoc_type_to_dart(param_type: str) -> str:
    """
    将 ShowDoc 参数类型映射到 Dart 类型
    
    Args:
        param_type: ShowDoc 参数类型（如 "string", "int", "boolean" 等）
    
    Returns:
        Dart 类型名称
    """
    param_type = (param_type or "").lower().strip()
    type_mapping = {
        "string": "String",
        "str": "String",
        "int": "int",
        "integer": "int",
        "long": "int",
        "float": "double",
        "double": "double",
        "boolean": "bool",
        "bool": "bool",
        "array": "List<dynamic>",
        "list": "List<dynamic>",
        "object": "Map<String, dynamic>",
        "json": "Map<String, dynamic>",
        "file": "dynamic",  # 文件上传，通常需要特殊处理
    }
    return type_mapping.get(param_type, "String")


def build_request_schema_from_params_dart(param_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    从参数列表构建请求实体类 Schema（Dart 版本）
    
    Args:
        param_list: 参数列表，每个参数包含 name, type, value, require 等字段
    
    Returns:
        Schema 字典，格式为 {字段名: {type: "类型", nullable: bool}}
    """
    schema = {}
    for param in param_list:
        if not isinstance(param, dict):
            continue
        
        name = param.get("name", "").strip()
        if not name:  # 忽略空名称
            continue
        
        param_type = param.get("type", "string")
        require = param.get("require", "1")  # "1" 表示必需，"0" 表示可选
        nullable = (require != "1")
        
        dart_type = _map_showdoc_type_to_dart(param_type)
        schema[name] = {
            "type": dart_type,
            "nullable": nullable
        }
    
    return schema


__all__ = [
    "extract_data_from_response",
    "extract_data_from_request",
    "analyze_entity_schema",
    "generate_nested_entity_name",
    "build_request_schema_from_params",
    "build_request_schema_from_params_dart",
    "sanitize_category_name",
    "_map_showdoc_type_to_dart",
]

