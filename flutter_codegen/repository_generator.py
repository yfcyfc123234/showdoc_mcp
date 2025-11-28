"""
Repository 生成器（Flutter 版本）

为 ApiService 中的每个 API 方法生成对应的 Repository 方法
"""
from typing import List, Dict, Any, Optional

from core.models import ApiDefinition


class FlutterRepositoryGenerator:
    """生成 Repository 类代码"""
    
    def __init__(self, base_package: str = "com.example.api"):
        """
        初始化生成器
        
        Args:
            base_package: Flutter 项目的基础包名
        """
        self.base_package = base_package
    
    def generate_repository(self, all_apis: List[Dict[str, Any]], available_entities: Optional[set] = None) -> str:
        """
        生成 Repository 类代码
        
        Args:
            all_apis: 所有 API 定义列表
            available_entities: 可用的实体类名称集合（用于检查实体类是否存在）
        
        Returns:
            生成的 Dart 代码字符串
        """
        # 保存可用实体类集合，用于检查实体类是否存在
        self.available_entities = available_entities or set()
        
        # 收集所有需要的分类
        categories = set()
        for api_data in all_apis:
            category = api_data.get("category")
            if category:
                categories.add(category.cat_name)
        
        # 生成导入语句
        import_lines = [
            f"import '{self.base_package}/models/response_data.dart';",
            f"import '{self.base_package}/services/api_service.dart';",
            "import 'package:dio/dio.dart';",
        ]
        
        # 为每个分类生成 request 和 response 包的导入
        from .entity_schema import sanitize_category_name
        for category_name in sorted(categories):
            category_package = sanitize_category_name(category_name)
            import_lines.append(f"import '{self.base_package}/models/{category_package}/request/request.dart';")
            import_lines.append(f"import '{self.base_package}/models/{category_package}/response/response.dart';")
        
        lines = import_lines + [
            "",
            "/// 自动生成的 Repository 类",
            "/// 由 ShowDoc 文档自动生成",
            "/// 所有响应都使用 ResponseData<T> 包装格式",
            "class ApiRepository {",
            "  final ApiService apiService;",
            "",
            "  ApiRepository(this.apiService);",
            "",
        ]
        
        # 为每个 API 生成对应的 Repository 方法
        for api_data in all_apis:
            api = api_data["api"]
            method_code = self._generate_repository_method(api, api_data)
            if method_code:
                lines.extend(method_code)
                lines.append("")  # 空行分隔
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _generate_repository_method(
        self,
        api: ApiDefinition,
        api_data: Dict[str, Any]
    ) -> List[str]:
        """生成 Repository 方法代码"""
        if not api.url:
            return []
        
        from .dio_service_generator import DioServiceGenerator
        
        # 复用 DioServiceGenerator 的方法提取逻辑
        dio_gen = DioServiceGenerator(self.base_package)
        dio_gen.available_entities = getattr(self, 'available_entities', set())
        method_name = dio_gen._generate_method_name(api, api_data.get("page"))
        return_type = dio_gen._generate_return_type(api, api_data.get("page"), api_data)
        
        lines = []
        
        # 添加注释
        page = api_data.get("page")
        category = api_data.get("category")
        
        lines.append("  ///")
        if api.title:
            lines.append(f"  /// {api.title}")
        if api.description:
            lines.append(f"  /// {api.description}")
        if page:
            lines.append(f"  /// 来源: {page.page_title}")
        lines.append("  ///")
        
        # 解析参数（复用 DioServiceGenerator 的逻辑）
        parsed_params = dio_gen._parse_parameters(api)
        
        # 生成方法签名参数列表
        method_params = []
        api_call_params = []
        
        # 路径参数
        if parsed_params.get("path"):
            for param in parsed_params["path"]:
                param_name = param["name"]
                param_type = param.get("type", "String")
                method_params.append(f"{param_type} {param_name}")
                api_call_params.append(f"{param_name}: {param_name}")
        
        # 查询参数
        if parsed_params.get("query"):
            for param in parsed_params["query"]:
                param_name = param["name"]
                param_type = param.get("type", "String")
                nullable = param.get("nullable", False)
                param_type_str = f"{param_type}{'?' if nullable else ''}"
                method_params.append(f"{param_type_str} {param_name}")
                api_call_params.append(f"{param_name}: {param_name}")
        
        # Body 对象参数（GET 请求不应该有 Body）
        if parsed_params.get("body") and not parsed_params.get("body_fields") and api.method.upper() != "GET":
            body_type = dio_gen._generate_body_type(api, api_data.get("page"), api_data)
            body_param_name = "body"
            method_params.append(f"{body_type}? {body_param_name}")
            api_call_params.append(f"{body_param_name}: {body_param_name}")
        
        # 生成方法签名
        method_signature = f"  Future<ResponseData<{return_type}>> {method_name}("
        if method_params:
            method_signature += ", ".join(method_params)
        method_signature += ") async {"
        lines.append(method_signature)
        
        # 生成 API 调用
        api_call = f"    return await apiService.{method_name}("
        if api_call_params:
            api_call += ", ".join(api_call_params)
        api_call += ");"
        lines.append(api_call)
        lines.append("  }")
        
        return lines

