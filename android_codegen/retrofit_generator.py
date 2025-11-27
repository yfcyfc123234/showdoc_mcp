"""
Retrofit2 Service 接口生成器

将 API 定义转换为 Retrofit2 接口代码
"""
from typing import List, Dict, Any, Optional
import re

from core.models import ApiDefinition
from .utils import sanitize_method_name, sanitize_class_name


class RetrofitServiceGenerator:
    """生成 Retrofit2 Service 接口代码"""
    
    def __init__(self, base_package: str = "com.example.api"):
        """
        初始化生成器
        
        Args:
            base_package: Android 项目的基础包名
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
        生成 Retrofit Service 接口代码
        
        Args:
            apis: API 定义列表，每个元素包含 api, page, category 信息
            available_entities: 可用的实体类名称集合（用于检查实体类是否存在）
            api_to_response_entity: API (url, method) -> 响应实体类名称的映射
            api_to_request_entity: API (url, method) -> 请求实体类名称的映射
        
        Returns:
            生成的 Kotlin 代码字符串
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
            f"package {self.base_package}.services",
            "",
            "import retrofit2.http.*",
            "import retrofit2.Call",
            "import retrofit2.Response",
            "import okhttp3.FormBody",
            f"import {self.base_package}.entities.ResponseData",
        ]
        
        # 为每个分类生成 request 和 response 包的导入
        from .entity_schema import sanitize_category_name
        for category_name in sorted(categories):
            category_package = sanitize_category_name(category_name)
            import_lines.append(f"import {self.base_package}.entities.{category_package}.request.*")
            import_lines.append(f"import {self.base_package}.entities.{category_package}.response.*")
        
        lines = import_lines + [
            "",
            "/**",
            " * 自动生成的 Retrofit Service 接口",
            " * 由 ShowDoc 文档自动生成",
            " * 所有响应都使用 ResponseData<T> 包装格式",
            " */",
            "interface ApiService {",
            ""
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
        
        lines.append("    /**")
        if api.title:
            lines.append(f"     * {api.title}")
        if api.description:
            lines.append(f"     * {api.description}")
        if page:
            lines.append(f"     * 来源: {page.page_title}")
        if category:
            lines.append(f"     * 分类: {category.cat_name}")
        lines.append(f"     * API: {api.method} {api.url}")
        lines.append("     */")
        
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
        body_fields_params = []
        body_params = []
        
        # 路径参数
        if params.get("path"):
            for param in params["path"]:
                param_name = param["name"]
                param_type = param.get("type", "String")
                path_params.append(f"        @Path(\"{param_name}\") {param_name}: {param_type}")
        
        # 查询参数
        if params.get("query"):
            for param in params["query"]:
                param_name = param["name"]
                param_type = param.get("type", "String")
                nullable = param.get("nullable", False)
                query_params.append(f"        @Query(\"{param_name}\") {param_name}: {param_type}{'?' if nullable else ''}")
        
        # Body 字段参数（如果少于5个简单字段）
        if params.get("body_fields"):
            for field in params["body_fields"]:
                field_name = field["name"]
                field_type = field["type"]
                # 使用 @Field 注解（POST/PUT/PATCH）或 @Query（GET）
                if api.method.upper() in ["GET"]:
                    body_fields_params.append(f"        @Query(\"{field_name}\") {field_name}: {field_type}")
                else:
                    body_fields_params.append(f"        @Field(\"{field_name}\") {field_name}: {field_type}")
        
        # Body 对象参数（GET 请求不应该有 Body）
        if params.get("body") and not params.get("body_fields") and api.method.upper() != "GET":
            body_type = self._generate_body_type(api, page, api_data)
            body_params.append(f"        @Body body: {body_type}")
        
        all_params = path_params + query_params + body_fields_params + body_params
        param_str = ",\n".join(all_params) if all_params else ""
        
        # 判断是否需要使用 @FormUrlEncoded（使用 @Field 时需要）
        needs_form_url_encoded = bool(params.get("body_fields")) and api.method.upper() in ["POST", "PUT", "PATCH"]
        
        # 生成返回类型（使用冲突解决后的名称）
        return_type = self._generate_return_type(api, page, api_data)
        
        # 生成 HTTP 注解
        http_annotation = self._generate_http_annotation(http_method, url_path, params)
        
        # 如果需要表单编码，添加 @FormUrlEncoded
        if needs_form_url_encoded:
            lines.append("    @FormUrlEncoded")
        
        lines.append(f"    {http_annotation}")
        lines.append(f"    suspend fun {method_name}(")
        if param_str:
            lines.append(param_str)
        # 使用 ResponseData 包装返回类型
        lines.append(f"    ): Response<ResponseData<{return_type}>>")
        
        return lines
    
    def _generate_method_name(self, api: ApiDefinition, page: Optional[Any]) -> str:
        """生成方法名（英文，优先从 URL 路径提取）"""
        from .utils import url_path_to_method_name, sanitize_method_name
        
        # 优先使用 URL 路径生成方法名
        url = api.url or ""
        if url:
            method_name = url_path_to_method_name(url)
            if method_name and method_name != "apiCall":
                return method_name
        
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
            # 找到协议后的域名部分，跳过它
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
                            "type": self._map_type_to_kotlin(param_type),
                            "nullable": param.get("required", True) == False
                        })
        
        # 解析请求体
        if api.body:
            body_data = api.body
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
                if len(simple_fields) < 5 and len(simple_fields) == len(body_fields):
                    params["body_fields"] = simple_fields
                else:
                    # 否则使用 body 对象
                    params["body"] = body_data
            else:
                params["body"] = body_data
        
        return params
    
    def _is_simple_type(self, value: Any) -> bool:
        """判断值是否是简单类型（字符串、数字、布尔值、None）"""
        return isinstance(value, (str, int, float, bool, type(None)))
    
    def _get_field_type(self, value: Any) -> str:
        """根据值推断字段类型"""
        if value is None:
            return "String?"
        elif isinstance(value, bool):
            return "Boolean"
        elif isinstance(value, int):
            return "Int"
        elif isinstance(value, float):
            return "Double"
        elif isinstance(value, str):
            return "String"
        else:
            return "Any"
    
    def _generate_http_annotation(
        self,
        method: str,
        path: str,
        params: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """生成 HTTP 方法注解"""
        url_path = path
        
        # 移除 {{baseurl}} 这种模板变量（这不是路径参数）
        url_path = url_path.replace("{{baseurl}}", "").replace("{{baseUrl}}", "").replace("{{BASEURL}}", "")
        
        # 清理多余的空格和斜杠
        url_path = url_path.strip().replace("//", "/")
        if not url_path.startswith("/"):
            url_path = "/" + url_path
        
        annotation_map = {
            "GET": "@GET",
            "POST": "@POST",
            "PUT": "@PUT",
            "DELETE": "@DELETE",
            "PATCH": "@PATCH"
        }
        
        annotation = annotation_map.get(method, "@GET")
        return f'{annotation}("{url_path}")'
    
    def _generate_return_type(self, api: ApiDefinition, page: Optional[Any] = None, api_data: Optional[Dict[str, Any]] = None) -> str:
        """生成返回类型（英文，优先从冲突解决后的映射获取）"""
        # 优先从映射中获取冲突解决后的实体类名称
        if api_data and hasattr(self, 'api_to_response_entity'):
            key = (api.url or "", api.method or "")
            entity_name = self.api_to_response_entity.get(key)
            if entity_name:
                return entity_name
        
        # 如果没有映射，使用原来的逻辑（向后兼容）
        from .utils import url_path_to_class_name, sanitize_class_name
        
        entity_name = None
        
        # 优先使用 URL 路径生成类名（data 字段的类型）
        url = api.url or ""
        if url:
            # 去掉 Response 后缀，因为会包装在 ResponseData 中
            class_name = url_path_to_class_name(url, "")
            if class_name and class_name != "Api":
                # 添加 Bean 后缀（用于混淆规则适配）
                if not class_name.endswith("Bean"):
                    class_name += "Bean"
                entity_name = class_name
        
        # 如果 URL 路径提取失败，尝试使用页面标题
        if not entity_name:
            title = api.title or ""
            if page and hasattr(page, 'page_title'):
                title = page.page_title or title
            
            if title:
                # 移除常见的后缀
                title = title.replace("-克隆", "").replace("-副本", "").replace("-复制", "")
                type_name = sanitize_class_name(title)
                # 去掉 Response 后缀
                if type_name.endswith("Response"):
                    type_name = type_name[:-8]  # 移除 "Response"
                # 添加 Bean 后缀（用于混淆规则适配）
                if type_name and type_name != "Any" and not type_name.endswith("Bean"):
                    type_name += "Bean"
                if type_name:
                    entity_name = type_name
        
        # 检查实体类是否存在（如果不存在，使用 Any 类型）
        if entity_name and hasattr(self, 'available_entities') and entity_name in self.available_entities:
            return entity_name
        
        # 如果实体类不存在或无法确定，使用 Any 类型
        return "Any"
    
    def _generate_body_type(self, api: ApiDefinition, page: Optional[Any] = None, api_data: Optional[Dict[str, Any]] = None) -> str:
        """生成请求体类型（英文，优先从冲突解决后的映射获取）"""
        # 优先从映射中获取冲突解决后的实体类名称
        if api_data and hasattr(self, 'api_to_request_entity'):
            key = (api.url or "", api.method or "")
            entity_name = self.api_to_request_entity.get(key)
            if entity_name:
                return entity_name
        
        # 如果没有映射，使用原来的逻辑（向后兼容）
        from .utils import url_path_to_class_name, sanitize_class_name
        
        # 优先使用 URL 路径生成类名
        url = api.url or ""
        if url:
            class_name = url_path_to_class_name(url, "Request")
            if class_name and class_name != "ApiRequest":
                return class_name
        
        # 如果 URL 路径提取失败，尝试使用页面标题
        title = api.title or ""
        if page and hasattr(page, 'page_title'):
            title = page.page_title or title
        
        if title:
            # 移除常见的后缀
            title = title.replace("-克隆", "").replace("-副本", "").replace("-复制", "")
            type_name = sanitize_class_name(title)
            if not type_name.endswith("Request"):
                type_name += "Request"
            # 添加 Bean 后缀（用于混淆规则适配）
            if not type_name.endswith("Bean"):
                type_name += "Bean"
            return type_name
        
        return "ApiRequestBean"
    
    def _map_type_to_kotlin(self, python_type: str) -> str:
        """将 Python 类型映射到 Kotlin 类型"""
        type_map = {
            "str": "String",
            "string": "String",
            "int": "Int",
            "integer": "Int",
            "float": "Double",
            "double": "Double",
            "bool": "Boolean",
            "boolean": "Boolean",
            "list": "List<Any>",
            "dict": "Map<String, Any>",
            "object": "Map<String, Any>"
        }
        
        python_type_lower = python_type.lower()
        return type_map.get(python_type_lower, "String")
    
    def _to_camel_case(self, text: str) -> str:
        """转换为驼峰命名（已废弃，使用 utils.sanitize_method_name）"""
        from .utils import sanitize_method_name
        return sanitize_method_name(text)

