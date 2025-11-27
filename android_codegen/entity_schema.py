"""
实体类 Schema 分析工具

从 responseOriginal.data 中提取并分析实体类结构，生成嵌套实体类
"""
from typing import Dict, Any, List, Optional, Set
import re


def extract_data_from_response(response: Dict[str, Any]) -> Optional[Any]:
    """
    从响应数据中提取 data 字段（忽略 ResponseData 包装层）
    
    Args:
        response: API 响应数据，可能包含 responseExample、responseOriginal 等字段
    
    Returns:
        data 字段的内容，如果不存在则返回 None
    """
    if not response:
        return None
    
    # 优先从 responseExample 中提取（JSON 字符串）
    if "responseExample" in response:
        import json
        try:
            response_example = response["responseExample"]
            if isinstance(response_example, str):
                parsed = json.loads(response_example)
                if isinstance(parsed, dict):
                    # 如果有 data 字段，返回 data 字段的内容（忽略 ResponseData 包装）
                    if "data" in parsed:
                        return parsed["data"]
                    # 如果没有 data 字段，检查是否是包装格式 {code, msg, data, hasNext}
                    if all(key in parsed for key in ["code", "msg"]):
                        # 可能有 data 字段或 hasNext，返回 data 字段
                        return parsed.get("data")
        except Exception as e:
            # 解析失败，继续尝试其他方式
            pass
    
    # 其次从 responseOriginal 中提取
    if "responseOriginal" in response:
        response_original = response["responseOriginal"]
        if isinstance(response_original, dict):
            # 如果有 data 字段，返回 data 字段的内容
            if "data" in response_original:
                return response_original["data"]
    
    # 从 responseText 中解析（JSON 字符串）
    if "responseText" in response:
        import json
        try:
            response_text = response["responseText"]
            if isinstance(response_text, str):
                parsed = json.loads(response_text)
                if isinstance(parsed, dict) and "data" in parsed:
                    return parsed["data"]
        except:
            pass
    
    # 从 example 或 body 中提取
    example = response.get("example") or response.get("body")
    if isinstance(example, dict):
        # 如果有 data 字段，返回 data 字段的内容
        if "data" in example:
            return example["data"]
        # 如果没有 data 字段，检查是否是包装格式
        if all(key in example for key in ["code", "msg"]):
            return example.get("data")
        # 否则返回整个 example（可能没有包装）
        return example
    
    # 如果 example 是字符串，尝试解析 JSON
    if isinstance(example, str):
        import json
        try:
            parsed = json.loads(example)
            if isinstance(parsed, dict) and "data" in parsed:
                return parsed["data"]
        except:
            pass
    
    return None


def analyze_entity_schema(data: Any, base_name: str = "Item") -> Dict[str, Any]:
    """
    分析数据并生成实体类 Schema（支持嵌套对象）
    
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
        """分析值并返回类型信息"""
        if value is None:
            return {"type": "Any?", "nullable": True, "nested": None}
        
        if isinstance(value, bool):
            return {"type": "Boolean", "nullable": False, "nested": None}
        elif isinstance(value, int):
            return {"type": "Int", "nullable": False, "nested": None}
        elif isinstance(value, float):
            return {"type": "Double", "nullable": False, "nested": None}
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
                        "type": f"MutableList<{nested_name}>",
                        "nullable": False,
                        "nested": nested_entity
                    }
                else:
                    # 确保基本类型也使用 MutableList
                    return {
                        "type": f"MutableList<{item_type}>",
                        "nullable": False,
                        "nested": None
                    }
            else:
                return {"type": "MutableList<Any>", "nullable": False, "nested": None}
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
            return {"type": "Any", "nullable": False, "nested": None}
    
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
            item_type = analyze_value(first_item, "")
            return {
                "schema": {},
                "nested": {}
            }
    else:
        return {"schema": {}, "nested": {}}


def generate_nested_entity_name(field_name: str, base_name: str) -> str:
    """
    生成嵌套实体类名称（会自动添加 Bean 后缀）
    
    Args:
        field_name: 字段名
        base_name: 基础类名
    
    Returns:
        嵌套实体类名称（带 Bean 后缀）
    """
    from .utils import sanitize_class_name
    
    # 移除 base_name 的 Bean 后缀（如果存在），因为我们要重新添加
    clean_base_name = base_name
    if clean_base_name.endswith("Bean"):
        clean_base_name = clean_base_name[:-4]
    
    if field_name:
        # 使用字段名生成类名
        class_name = sanitize_class_name(field_name)
        # 添加 Bean 后缀（用于混淆规则适配）
        if not class_name.endswith("Bean"):
            class_name = class_name + "Bean"
        return class_name
    else:
        # 使用基础类名 + Item + Bean
        return f"{clean_base_name}ItemBean"


def _map_showdoc_type_to_kotlin(param_type: str) -> str:
    """
    将 ShowDoc 参数类型映射到 Kotlin 类型
    
    Args:
        param_type: ShowDoc 参数类型（如 "string", "int", "boolean" 等）
    
    Returns:
        Kotlin 类型名称
    """
    param_type = (param_type or "").lower().strip()
    type_mapping = {
        "string": "String",
        "str": "String",
        "int": "Int",
        "integer": "Int",
        "long": "Long",
        "float": "Float",
        "double": "Double",
        "boolean": "Boolean",
        "bool": "Boolean",
        "array": "MutableList<Any>",
        "list": "MutableList<Any>",
        "object": "Any",
        "json": "Any",
        "file": "Any",  # 文件上传，通常需要特殊处理
    }
    return type_mapping.get(param_type, "String")


def build_request_schema_from_params(param_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    从参数列表构建请求实体类 Schema
    
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
        
        kotlin_type = _map_showdoc_type_to_kotlin(param_type)
        schema[name] = {
            "type": kotlin_type,
            "nullable": nullable
        }
    
    return schema


def extract_data_from_request(params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    从 ShowDoc 的请求参数结构中提取实际的请求参数或参数列表
    
    ShowDoc 的 api.body 包含：
    {
        "mode": "urlencoded" | "formdata" | "json",
        "urlencoded": [...],  # 参数列表
        "formdata": [...],    # 参数列表
        "json": "...",        # JSON 字符串
        "jsonDesc": [...]     # JSON 参数描述列表
    }
    
    Args:
        params: ShowDoc 的 params 对象（api.body）
    
    Returns:
        - 如果是 JSON 模式：返回解析后的 JSON 对象（字典）
        - 如果是 urlencoded/formdata 模式：返回参数列表（用于后续构建 schema）
        - 如果无法提取：返回 None
    """
    if not params or not isinstance(params, dict):
        return None
    
    # 检查是否是 ShowDoc 的 params 结构（包含 mode 字段）
    mode = params.get("mode", "").lower()
    
    # 如果包含 mode 字段，说明这是 ShowDoc 的 params 结构，需要提取实际参数
    if mode:
        # 根据 mode 选择参数来源
        if mode == "json":
            # JSON 模式：从 json 字段或 jsonDesc 中提取
            json_str = params.get("json", "")
            json_desc = params.get("jsonDesc", [])
            
            # 优先使用 json 字段（如果有有效的 JSON）
            if json_str and json_str.strip():
                import json
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict):
                        return parsed
                except:
                    pass
            
            # 如果没有有效的 json 字符串，尝试从 jsonDesc 构建
            # 但 jsonDesc 通常是扁平化的参数列表，需要特殊处理
            if json_desc and isinstance(json_desc, list) and json_desc:
                # 标记为参数列表格式
                return {"__param_list__": json_desc, "__mode__": "json"}
            
            return None
        
        elif mode == "urlencoded":
            # URL 编码模式：从 urlencoded 列表中提取
            urlencoded = params.get("urlencoded", [])
            if urlencoded and isinstance(urlencoded, list):
                # 过滤掉空名称和已禁用的参数
                valid_params = []
                for item in urlencoded:
                    if isinstance(item, dict):
                        name = item.get("name", "").strip()
                        disable = item.get("disable", "0")
                        if name and disable != "1":
                            valid_params.append(item)
                
                if valid_params:
                    # 标记为参数列表格式
                    return {"__param_list__": valid_params, "__mode__": "urlencoded"}
            
            return None
        
        elif mode == "formdata":
            # 表单数据模式：从 formdata 列表中提取
            formdata = params.get("formdata", [])
            if formdata and isinstance(formdata, list):
                # 过滤掉空名称
                valid_params = []
                for item in formdata:
                    if isinstance(item, dict):
                        name = item.get("name", "").strip()
                        if name:
                            valid_params.append(item)
                
                if valid_params:
                    # 标记为参数列表格式
                    return {"__param_list__": valid_params, "__mode__": "formdata"}
            
            return None
        
        # 如果没有匹配的模式，返回 None
        return None
    
    # 如果没有 mode 字段，可能是直接的参数字典，直接返回
    # 但需要过滤掉 ShowDoc 的元数据字段
    showdoc_meta_fields = {"mode", "urlencoded", "formdata", "json", "jsonDesc"}
    filtered = {k: v for k, v in params.items() if k not in showdoc_meta_fields}
    return filtered if filtered else None


def sanitize_category_name(cat_name: str) -> str:
    """
    清理分类名称，用于文件夹名称和包名（必须全部是英文）
    
    Args:
        cat_name: 分类名称（可能是中文）
    
    Returns:
        清理后的文件夹名称（全英文，小写）
    """
    from .utils import translate_chinese_to_english
    
    # 先转换为英文
    name = translate_chinese_to_english(cat_name)
    
    if not name:
        return "default"
    
    # 移除特殊字符，只保留字母、数字、下划线
    name = re.sub(r'[^a-zA-Z0-9_]', '', name)
    
    # 确保是有效的包名（不能以数字开头）
    if name and name[0].isdigit():
        name = "cat_" + name
    
    if not name or not name.isascii():
        return "default"
    
    return name.lower()

