"""
Repository 生成器

为 ApiService 中的每个 API 方法生成对应的 Repository 方法
"""
from typing import List, Dict, Any, Optional
import re

from core.models import ApiDefinition


class RepositoryGenerator:
    """生成 Repository 类代码"""
    
    def __init__(self, base_package: str = "com.example.api"):
        """
        初始化生成器
        
        Args:
            base_package: Android 项目的基础包名
        """
        self.base_package = base_package
    
    def generate_repository(self, all_apis: List[Dict[str, Any]], available_entities: Optional[set] = None) -> str:
        """
        生成 Repository 类代码
        
        Args:
            all_apis: 所有 API 定义列表
            available_entities: 可用的实体类名称集合（用于检查实体类是否存在）
        
        Returns:
            生成的 Kotlin 代码字符串
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
            f"package {self.base_package}.repository",
            "",
            f"import {self.base_package}.entities.ResponseData",
            f"import {self.base_package}.services.ApiService",
            "import kotlinx.coroutines.Dispatchers",
            "import kotlinx.coroutines.withContext",
            "import retrofit2.Response",
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
            " * 自动生成的 Repository 类",
            " * 由 ShowDoc 文档自动生成",
            " * 所有响应都使用 ResponseData<T> 包装格式",
            " */",
            "open class ApiRepository(",
            "    private val apiService: ApiService",
            ") {",
            "",
            "    /**",
            "     * 通用请求方法",
            "     * 处理响应并提取 ResponseData",
            "     */",
            "    private suspend fun <T> request(",
            "        call: suspend () -> Response<ResponseData<T>>",
            "    ): ResponseData<T> {",
            "        return withContext(Dispatchers.IO) {",
            "            val response = call.invoke()",
            "            if (response.isSuccessful && response.body() != null) {",
            "                response.body()!!",
            "            } else {",
            "                // 处理错误响应",
            "                ResponseData(",
            "                    code = response.code(),",
            "                    msg = response.message() ?: \"请求失败\",",
            "                    data = null as T,",
            "                    hasNext = 0",
            "                )",
            "            }",
            "        }.apply {",
            "            // 处理登录过期等业务逻辑",
            "            if (code == 201 || code == 202) {",
            "                // 登录过期，可以在这里处理",
            "            }",
            "        }",
            "    }",
            "",
            "    companion object {",
            "        @Volatile",
            "        private var INSTANCE: ApiRepository? = null",
            "",
            "        fun getInstance(apiService: ApiService): ApiRepository {",
            "            return INSTANCE ?: synchronized(this) {",
            "                INSTANCE ?: ApiRepository(apiService).also { INSTANCE = it }",
            "            }",
            "        }",
            "    }",
            ""
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
        
        from .retrofit_generator import RetrofitServiceGenerator
        
        # 复用 RetrofitServiceGenerator 的方法提取逻辑
        retrofit_gen = RetrofitServiceGenerator(self.base_package)
        # 传递 available_entities，用于检查实体类是否存在
        retrofit_gen.available_entities = getattr(self, 'available_entities', set())
        method_name = retrofit_gen._generate_method_name(api, api_data.get("page"))
        return_type = retrofit_gen._generate_return_type(api, api_data.get("page"))
        
        lines = []
        
        # 添加注释
        page = api_data.get("page")
        category = api_data.get("category")
        
        lines.append("    /**")
        if api.title:
            lines.append(f"     * {api.title}")
        if api.description:
            lines.append(f"     * {api.description}")
        if page:
            lines.append(f"     * 来源: {page.page_title}")
        lines.append("     */")
        
        # 解析参数（复用 RetrofitServiceGenerator 的逻辑）
        parsed_params = retrofit_gen._parse_parameters(api)
        
        # 生成方法签名参数列表
        method_params = []
        api_call_params = []
        
        # 路径参数
        if parsed_params.get("path"):
            for param in parsed_params["path"]:
                param_name = param["name"]
                param_type = param.get("type", "String")
                method_params.append(f"{param_name}: {param_type}")
                api_call_params.append(f"{param_name} = {param_name}")
        
        # 查询参数
        if parsed_params.get("query"):
            for param in parsed_params["query"]:
                param_name = param["name"]
                param_type = param.get("type", "String")
                nullable = param.get("nullable", False)
                param_type_str = f"{param_type}{'?' if nullable else ''}"
                method_params.append(f"{param_name}: {param_type_str}")
                api_call_params.append(f"{param_name} = {param_name}")
        
        # Body 字段参数（如果少于5个简单字段）
        if parsed_params.get("body_fields"):
            for field in parsed_params["body_fields"]:
                field_name = field["name"]
                field_type = field.get("type", "String")
                method_params.append(f"{field_name}: {field_type}")
                api_call_params.append(f"{field_name} = {field_name}")
        
        # Body 对象参数（GET 请求不应该有 Body）
        if parsed_params.get("body") and not parsed_params.get("body_fields") and api.method.upper() != "GET":
            body_type = retrofit_gen._generate_body_type(api, api_data.get("page"))
            body_param_name = "body"
            method_params.append(f"{body_param_name}: {body_type}")
            api_call_params.append(f"body = {body_param_name}")
        
        # 生成方法签名
        method_signature = f"    suspend fun {method_name}("
        if method_params:
            method_signature += ", ".join(method_params)
        method_signature += f"): ResponseData<{return_type}> = request {{"
        lines.append(method_signature)
        
        # 生成 API 调用
        api_call = f"        apiService.{method_name}("
        if api_call_params:
            api_call += ", ".join(api_call_params)
        api_call += ")"
        lines.append(api_call)
        lines.append("    }")
        
        return lines

