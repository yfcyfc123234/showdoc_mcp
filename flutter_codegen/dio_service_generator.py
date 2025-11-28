"""
Dio Service 生成器

将 API 定义转换为 Dio Service 代码
"""
from typing import List, Dict, Any, Optional
import re

from core.models import ApiDefinition
from .utils import sanitize_method_name, sanitize_class_name, url_path_to_method_name


class DioServiceGenerator:
    """生成 Dio Service 代码"""
    
    def __init__(self, base_package: str = "com.example.api"):
        """
        初始化生成器
        
        Args:
            base_package: Flutter 项目的基础包名
        """
        self.base_package = base_package
    
    def generate_services(
        self, 
        apis: List[Dict[str, Any]], 
        available_entities: Optional[set] = None,
        api_to_response_entity: Optional[Dict[tuple, str]] = None,
        api_to_request_entity: Optional[Dict[tuple, str]] = None
    ) -> str:
        """
        生成 Dio Service 代码
        
        Args:
            apis: API 定义列表，每个元素包含 api, page, category 信息
            available_entities: 可用的实体类名称集合（用于检查实体类是否存在）
            api_to_response_entity: API (url, method) -> 响应实体类名称的映射
            api_to_request_entity: API (url, method) -> 请求实体类名称的映射
        
        Returns:
            生成的 Dart 代码字符串
        """
        # 保存可用实体类集合，用于检查实体类是否存在
        self.available_entities = available_entities or set()
        # 保存映射关系
        self.api_to_response_entity = api_to_response_entity or {}
        self.api_to_request_entity = api_to_request_entity or {}
        
        # 收集所有需要的分类和实体类型
        categories = set()
        for api_data in apis:
            category = api_data.get("category")
            if category:
                categories.add(category.cat_name)
        
        # 生成导入语句
        import_lines = [
            "import 'package:dio/dio.dart';",
            "import '../models/response_data.dart';",
        ]
        
        # 为每个分类生成 request 和 response 包的导入
        from .entity_schema import sanitize_category_name
        for category_name in sorted(categories):
            category_package = sanitize_category_name(category_name)
            import_lines.append(f"import '../models/{category_package}/request/request.dart';")
            import_lines.append(f"import '../models/{category_package}/response/response.dart';")
        
        lines = import_lines + [
            "",
            "/// 自动生成的 Dio Service 类",
            "/// 由 ShowDoc 文档自动生成",
            "/// 所有响应都使用 ResponseData<T> 包装格式",
            "abstract class ApiService {",
            "  final Dio dio;",
            "",
            "  ApiService(this.dio);",
            "",
        ]
        
        # 为每个 API 生成方法
        for api_data in apis:
            api = api_data["api"]
            method_code = self._generate_method(api, api_data)
            if method_code:
                lines.extend(method_code)
                lines.append("")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _generate_method(self, api: ApiDefinition, api_data: Dict[str, Any]) -> List[str]:
        """
        生成单个 API 方法
        
        Args:
            api: API 定义
            api_data: 包含 page 和 category 信息的字典
        
        Returns:
            方法代码行列表
        """
        if not api.url:
            return []
        
        lines = []
        
        # 生成方法注释
        page = api_data.get("page")
        category = api_data.get("category")
        
        lines.append("  ///")
        if api.title:
            lines.append(f"  /// {api.title}")
        if api.description:
            lines.append(f"  /// {api.description}")
        if page:
            lines.append(f"  /// 来源: {page.page_title}")
        if category:
            lines.append(f"  /// 分类: {category.cat_name}")
        lines.append(f"  /// API: {api.method} {api.url}")
        lines.append("  ///")
        
        # 生成方法签名
        method_name = self._generate_method_name(api, page)
        http_method = api.method.upper()
        url_path = self._extract_path(api.url)
        
        # 解析参数
        params = self._parse_parameters(api)
        
        # 生成参数列表
        param_list = []
        query_params = []
        path_params = []
        body_params = []
        
        # 路径参数
        if params.get("path"):
            for param in params["path"]:
                param_name = param["name"]
                param_type = param.get("type", "String")
                path_params.append(f"{param_type} {param_name}")
                param_list.append(f"{param_type} {param_name}")
        
        # 查询参数
        if params.get("query"):
            for param in params["query"]:
                param_name = param["name"]
                param_type = param.get("type", "String")
                nullable = param.get("nullable", False)
                param_type_str = f"{param_type}{'?' if nullable else ''}"
                query_params.append(f"{param_name}: {param_type_str}")
                param_list.append(f"{param_type_str} {param_name}")
        
        # Body 对象参数（GET 请求不应该有 Body）
        if params.get("body") and not params.get("body_fields") and api.method.upper() != "GET":
            body_type = self._generate_body_type(api, page, api_data)
            body_params.append(f"{body_type}? body")
            param_list.append(f"{body_type}? body")
        
        # 生成返回类型（使用冲突解决后的名称）
        return_type = self._generate_return_type(api, page, api_data)
        
        # 生成方法签名
        method_signature = f"  Future<ResponseData<{return_type}>> {method_name}("
        if param_list:
            method_signature += ", ".join(param_list)
        method_signature += ") async {"
        lines.append(method_signature)
        
        # 构建 URL（处理路径参数）
        url = url_path
        if path_params:
            for param in params["path"]:
                param_name = param["name"]
                url = url.replace(f"{{{param_name}}}", "${{$param_name}}")
        
        # 生成请求代码
        lines.append(f"    final response = await dio.{http_method.lower()}(")
        lines.append(f"      '{url}',")
        
        # 查询参数
        if query_params:
            lines.append("      queryParameters: {")
            for param in params["query"]:
                param_name = param["name"]
                lines.append(f"        '{param_name}': {param_name},")
            lines.append("      },")
        
        # Body 参数
        if body_params:
            lines.append("      data: body?.toJson(),")
        
        lines.append("    );")
        lines.append(f"    return ResponseData<{return_type}>.fromJson(")
        lines.append(f"      response.data,")
        lines.append(f"      (json) => {return_type}.fromJson(json as Map<String, dynamic>),")
        lines.append(f"    );")
        lines.append("  }")
        
        return lines
    
    def _generate_method_name(self, api: ApiDefinition, page: Optional[Any]) -> str:
        """生成方法名（英文，优先从 URL 路径提取）"""
        # 优先使用 URL 路径生成方法名
        url = api.url or ""
        if url:
            method_name = url_path_to_method_name(url)
            if method_name and method_name != "apiCall":
                return sanitize_method_name(method_name)
        
        # 如果 URL 路径提取失败，尝试使用页面标题
        if page and page.page_title:
            title = page.page_title.replace("-克隆", "").replace("-副本", "").replace("-复制", "")
            return sanitize_method_name(title)
        
        # 使用 API 标题
        if api.title:
            return sanitize_method_name(api.title)
        
        # 默认方法名
        method = api.method.lower()
        return f"{method}Request"
    
    def _extract_path(self, url: str) -> str:
        """从完整 URL 中提取路径部分"""
        if not url:
            return "/"
        
        # 处理 {{baseurl}} 这种格式，转换为路径参数
        url = url.replace("{{baseurl}}", "").replace("{{baseUrl}}", "").strip()
        
        # 移除协议和域名
        if "://" in url:
            parts = url.split("/")
            url = "/" + "/".join(parts[3:]) if len(parts) > 3 else "/"
        
        # 移除查询参数
        if "?" in url:
            url = url.split("?")[0]
        
        # 确保以 / 开头
        if not url.startswith("/"):
            url = "/" + url
        
        return url
    
    def _parse_parameters(self, api: ApiDefinition) -> Dict[str, List[Dict[str, Any]]]:
        """解析 API 参数"""
        params = {
            "path": [],
            "query": [],
            "body_fields": [],  # body 中的字段（如果作为单独参数）
            "body": None  # body 对象（如果作为整体）
        }
        
        # 解析路径参数（排除 baseurl 等模板变量）
        url = api.url or ""
        path_params = re.findall(r'\{(\w+)\}', url)
        # 过滤掉模板变量（baseurl, baseUrl 等）
        template_vars = {"baseurl", "baseUrl", "BASEURL"}
        for param_name in path_params:
            if param_name.lower() not in template_vars:
                params["path"].append({
                    "name": param_name,
                    "type": "String"
                })
        
        # 解析查询参数
        if api.query:
            for param in api.query:
                if isinstance(param, dict):
                    param_name = param.get("name") or param.get("key")
                    param_type = param.get("type", "String")
                    if param_name:
                        params["query"].append({
                            "name": param_name,
                            "type": self._map_type_to_dart(param_type),
                            "nullable": param.get("required", True) == False
                        })
        
        # 解析请求体
        if api.body:
            from .entity_schema import extract_data_from_request
            body_data = extract_data_from_request(api.body)
            if isinstance(body_data, dict) and body_data:
                # 判断是否将 body 字段作为单独参数
                body_fields = list(body_data.keys())
                simple_fields = []
                
                # 检查字段是否是简单类型（字符串、数字、布尔值）
                for field_name, field_value in body_data.items():
                    if self._is_simple_type(field_value):
                        simple_fields.append({
                            "name": field_name,
                            "value": field_value,
                            "type": self._get_field_type(field_value)
                        })
                
                # 如果简单字段少于5个，将它们作为单独参数
                if len(simple_fields) < 5:
                    params["body_fields"] = simple_fields
                else:
                    # 否则作为整体对象
                    params["body"] = body_data
        
        return params
    
    def _is_simple_type(self, value: Any) -> bool:
        """判断是否是简单类型"""
        return isinstance(value, (str, int, float, bool)) or value is None
    
    def _get_field_type(self, value: Any) -> str:
        """根据值推断字段类型"""
        if value is None:
            return "String?"
        elif isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "double"
        elif isinstance(value, str):
            return "String"
        else:
            return "dynamic"
    
    def _map_type_to_dart(self, param_type: str) -> str:
        """将参数类型映射到 Dart 类型"""
        from .entity_schema import _map_showdoc_type_to_dart
        return _map_showdoc_type_to_dart(param_type)
    
    def _generate_return_type(self, api: ApiDefinition, page: Optional[Any], api_data: Dict[str, Any]) -> str:
        """生成返回类型"""
        # 使用映射关系获取响应实体类名称
        api_key = (api.url or "", api.method or "")
        entity_name = self.api_to_response_entity.get(api_key)
        
        if entity_name and entity_name in self.available_entities:
            return entity_name
        
        # 如果没有映射，尝试从 URL 生成
        from .utils import url_path_to_class_name
        url = api.url or ""
        if url:
            class_name = url_path_to_class_name(url, "", depth=1)
            if class_name and class_name != "Api":
                return class_name
        
        # 默认返回类型
        return "dynamic"
    
    def _generate_body_type(self, api: ApiDefinition, page: Optional[Any], api_data: Dict[str, Any]) -> str:
        """生成请求体类型"""
        # 使用映射关系获取请求实体类名称
        api_key = (api.url or "", api.method or "")
        entity_name = self.api_to_request_entity.get(api_key)
        
        if entity_name and entity_name in self.available_entities:
            return entity_name
        
        # 如果没有映射，尝试从 URL 生成
        from .utils import url_path_to_class_name
        url = api.url or ""
        if url:
            class_name = url_path_to_class_name(url, "Request", depth=1)
            if class_name and class_name != "ApiRequest":
                return class_name
        
        # 默认请求体类型
        return "Map<String, dynamic>"

