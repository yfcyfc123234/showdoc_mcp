"""
Flutter 实体类生成器

将 API 响应数据转换为 Dart 类（使用 json_serializable）
"""
from typing import Dict, Any, Optional
import json

from .utils import sanitize_class_name, sanitize_field_name


class FlutterEntityGenerator:
    """生成 Flutter 实体类（使用 json_serializable）代码"""
    
    def __init__(self, base_package: str = "com.example.api"):
        """
        初始化生成器
        
        Args:
            base_package: Flutter 项目的基础包名
        """
        self.base_package = base_package
    
    def generate_entity(
        self,
        entity_name: str,
        schema: Dict[str, Any],
        category_name: str = "",
        nested_entities: Optional[Dict[str, Dict[str, Any]]] = None,
        entity_type: str = "",  # "request" 或 "response"
        api_data: Optional[Dict[str, Any]] = None,
        item_id: Optional[str] = None,
        server_base: Optional[str] = None
    ) -> str:
        """
        生成实体类代码
        
        Args:
            entity_name: 实体类名称
            schema: 实体类结构定义
            category_name: 分类名称（用于包名）
            nested_entities: 嵌套实体类定义
            entity_type: 实体类型（"request" 或 "response"），用于区分包名
            api_data: API 数据（包含 page、api 等信息），用于生成文档链接和响应示例
            item_id: ShowDoc 项目 ID，用于生成文档链接
            server_base: ShowDoc 服务器地址，用于生成文档链接
        
        Returns:
            生成的 Dart 代码字符串
        """
        if nested_entities is None:
            nested_entities = {}
        
        # 如果没有指定 entity_type，根据实体名称推断
        if not entity_type:
            if entity_name.endswith("Request"):
                entity_type = "request"
            else:
                entity_type = "response"
        
        # 确定包名（如果有分类，添加到包名中，并添加 request/response 子包）
        if category_name:
            from .entity_schema import sanitize_category_name
            category_package = sanitize_category_name(category_name)
            package_name = f"{self.base_package}.models.{category_package}.{entity_type}"
        else:
            package_name = f"{self.base_package}.models.{entity_type}"
        
        lines = [
            f"import 'package:json_annotation/json_annotation.dart';",
            "",
            f"part '{entity_name.lower()}.g.dart';",
            "",
        ]
        
        # 添加嵌套实体类的导入（如果需要）
        if nested_entities:
            for nested_name in nested_entities.keys():
                # 嵌套实体类在同一文件中定义，不需要导入
        
        # 生成文档注释
        lines.append("///")
        if api_data:
            api = api_data.get("api")
            page = api_data.get("page")
            if api and api.title:
                lines.append(f"/// {api.title}")
            if api and api.description:
                lines.append(f"/// {api.description}")
            if page:
                lines.append(f"/// 来源: {page.page_title}")
            # 生成文档链接
            if item_id and server_base and page:
                page_id = getattr(page, 'page_id', None)
                if page_id:
                    doc_url = f"{server_base}/web/#/{item_id}/{page_id}"
                    lines.append(f"/// 文档: {doc_url}")
        lines.append("/// 自动生成的实体类")
        lines.append("/// 由 ShowDoc 文档自动生成")
        lines.append("///")
        lines.append("")
        
        # 生成类定义
        lines.append("@JsonSerializable()")
        lines.append(f"class {entity_name} {{")
        lines.append("")
        
        # 生成字段
        if schema:
            for field_name, field_info in schema.items():
                field_type = field_info.get("type", "dynamic")
                nullable = field_info.get("nullable", False)
                
                # 清理字段名
                clean_field_name = sanitize_field_name(field_name)
                
                # 生成字段定义
                type_str = f"{field_type}{'?' if nullable else ''}"
                lines.append(f"  final {type_str} {clean_field_name};")
        
        # 生成构造函数
        constructor_params = []
        if schema:
            for field_name, field_info in schema.items():
                clean_field_name = sanitize_field_name(field_name)
                field_type = field_info.get("type", "dynamic")
                nullable = field_info.get("nullable", False)
                type_str = f"{field_type}{'?' if nullable else ''}"
                constructor_params.append(f"    {type_str} this.{clean_field_name},")
        
        lines.append("")
        lines.append(f"  {entity_name}(")
        if constructor_params:
            lines.extend(constructor_params)
        lines.append("  );")
        lines.append("")
        
        # 生成 fromJson 方法
        lines.append(f"  factory {entity_name}.fromJson(Map<String, dynamic> json) =>")
        lines.append(f"      _${entity_name}FromJson(json);")
        lines.append("")
        
        # 生成 toJson 方法
        lines.append(f"  Map<String, dynamic> toJson() => _${entity_name}ToJson(this);")
        lines.append("")
        
        # 生成嵌套实体类（在同一文件中）
        if nested_entities:
            lines.append("")
            for nested_name, nested_schema in nested_entities.items():
                nested_lines = self._generate_nested_entity(nested_name, nested_schema)
                lines.extend(nested_lines)
                lines.append("")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _generate_nested_entity(self, entity_name: str, schema: Dict[str, Any]) -> List[str]:
        """生成嵌套实体类"""
        lines = []
        
        lines.append(f"@JsonSerializable()")
        lines.append(f"class {entity_name} {{")
        lines.append("")
        
        # 生成字段
        for field_name, field_info in schema.items():
            field_type = field_info.get("type", "dynamic")
            nullable = field_info.get("nullable", False)
            clean_field_name = sanitize_field_name(field_name)
            type_str = f"{field_type}{'?' if nullable else ''}"
            lines.append(f"  final {type_str} {clean_field_name};")
        
        # 生成构造函数
        constructor_params = []
        for field_name, field_info in schema.items():
            clean_field_name = sanitize_field_name(field_name)
            field_type = field_info.get("type", "dynamic")
            nullable = field_info.get("nullable", False)
            type_str = f"{field_type}{'?' if nullable else ''}"
            constructor_params.append(f"    {type_str} this.{clean_field_name},")
        
        lines.append("")
        lines.append(f"  {entity_name}(")
        if constructor_params:
            lines.extend(constructor_params)
        lines.append("  );")
        lines.append("")
        
        # 生成 fromJson 和 toJson
        lines.append(f"  factory {entity_name}.fromJson(Map<String, dynamic> json) =>")
        lines.append(f"      _${entity_name}FromJson(json);")
        lines.append("")
        lines.append(f"  Map<String, dynamic> toJson() => _${entity_name}ToJson(this);")
        
        return lines
    
    def generate_response_data_base_class(self) -> str:
        """生成通用的 ResponseData 基类"""
        lines = [
            f"import 'package:json_annotation/json_annotation.dart';",
            "",
            f"part 'response_data.g.dart';",
            "",
            "/// 通用的响应数据包装类",
            "/// 所有 API 响应都使用此格式包装",
            "@JsonSerializable(genericArgumentFactories: true)",
            "class ResponseData<T> {",
            "  final int code;",
            "  final String msg;",
            "  final T? data;",
            "  final int hasNext;",
            "",
            "  ResponseData({",
            "    required this.code,",
            "    required this.msg,",
            "    this.data,",
            "    this.hasNext = 0,",
            "  });",
            "",
            "  factory ResponseData.fromJson(",
            "    Map<String, dynamic> json,",
            "    T Function(Object?) fromJsonT,",
            "  ) =>",
            "      _\$ResponseDataFromJson(json, fromJsonT);",
            "",
            "  Map<String, dynamic> toJson(Object? Function(T) toJsonT) =>",
            "      _\$ResponseDataToJson(this, toJsonT);",
            "}",
        ]
        
        return "\n".join(lines)

