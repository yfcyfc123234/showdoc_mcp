"""
Android 实体类生成器

将 API 响应数据转换为 Kotlin Data Class
"""
from typing import Dict, Any, Optional
import json
from .utils import sanitize_class_name


class AndroidEntityGenerator:
    """生成 Android 实体类（Data Class）代码"""
    
    def __init__(self, base_package: str = "com.example.api"):
        """
        初始化生成器
        
        Args:
            base_package: Android 项目的基础包名
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
            生成的 Kotlin 代码字符串
        """
        if nested_entities is None:
            nested_entities = {}
        
        # 确保实体类名称以 Bean 结尾（用于混淆规则适配）
        if not entity_name.endswith("Bean"):
            entity_name = entity_name + "Bean"
        
        # 如果没有指定 entity_type，根据实体名称推断（支持 Bean 后缀）
        if not entity_type:
            if entity_name.endswith("RequestBean"):
                entity_type = "request"
            else:
                entity_type = "response"
        
        # 确定包名（如果有分类，添加到包名中，并添加 request/response 子包）
        if category_name:
            from .entity_schema import sanitize_category_name
            category_package = sanitize_category_name(category_name)
            package_name = f"{self.base_package}.entities.{category_package}.{entity_type}"
        else:
            package_name = f"{self.base_package}.entities.{entity_type}"
        
        lines = [
            f"package {package_name}",
            "",
            "import android.os.Parcelable",
            "import kotlinx.parcelize.Parcelize",
        ]
        
        # 如果实体类中有 MutableList，需要添加导入
        if schema or nested_entities:
            needs_mutable_list = False
            # 检查 schema 中是否有 List 或 MutableList
            for value_info in schema.values():
                prop_type = value_info.get("type", "")
                if "MutableList" in prop_type or "List" in prop_type:
                    needs_mutable_list = True
                    break
            
            # 检查嵌套实体类中是否有 List
            if not needs_mutable_list:
                for nested_schema in nested_entities.values():
                    for value_info in nested_schema.values():
                        prop_type = value_info.get("type", "")
                        if "MutableList" in prop_type or "List" in prop_type:
                            needs_mutable_list = True
                            break
                    if needs_mutable_list:
                        break
            
            if needs_mutable_list:
                lines.append("import kotlin.collections.MutableList")
        
        # 嵌套实体类在同一个包中，不需要导入
        # 构建注释内容（包含文档链接和响应示例）
        
        # 获取中文名称（优先从 page.page_title 获取，其次从 api.title 获取）
        chinese_name = self._extract_chinese_name(api_data, entity_name)
        
        # 如果中文名称和英文类名相同，只显示一行
        if chinese_name == entity_name:
            title_line = f" * {chinese_name}"
        else:
            title_line = f" * {chinese_name} ({entity_name})"
        
        comment_lines = [
            "",
            "/**",
            title_line,
        ]
        
        # 添加文档链接（如果有）
        doc_url = self._build_document_url(api_data, item_id, server_base)
        if doc_url:
            comment_lines.append(f" * ")
            comment_lines.append(f" * 接口文档: {doc_url}")
        
        # 添加响应示例（仅对 response 实体类）
        if entity_type == "response" and api_data:
            response_example = self._extract_response_example(api_data)
            if response_example:
                comment_lines.append(f" * ")
                comment_lines.append(f" * 成功返回示例:")
                # 格式化 JSON 为多行注释
                formatted_example = self._format_json_for_comment(response_example)
                for line in formatted_example.split('\n'):
                    # 每行都添加注释标记（包括空行，保持 JSON 缩进）
                    comment_lines.append(f" * {line}")
        
        comment_lines.append(" */")
        lines.extend(comment_lines)
        lines.extend([
            "@Parcelize",
            f"data class {entity_name}("
        ])
        
        # 生成属性
        if schema:
            properties = []
            for key, value_info in schema.items():
                prop_type = value_info.get("type", "String")
                nullable = value_info.get("nullable", False)
                
                # 直接使用原字段名，不做任何转换（保持与服务器一致）
                # 如果字段名是 Kotlin 关键字，需要进行转义
                property_name = self._escape_kotlin_keyword(key)
                
                property_code = f"    var {property_name}: {prop_type}{'?' if nullable else ''}"
                properties.append(property_code)
            
            # 添加属性，最后一个不加逗号
            for i, prop in enumerate(properties):
                if i < len(properties) - 1:
                    lines.append(prop + ",")
                else:
                    lines.append(prop)
        else:
            # 如果没有 schema，生成一个空的实体类
            lines.append("    // TODO: 根据实际响应数据添加属性")
        
        lines.append(") : Parcelable")
        
        # 如果有嵌套实体类，在同一个文件中生成它们
        if nested_entities:
            lines.append("")  # 空行分隔
            
            for nested_name, nested_schema in nested_entities.items():
                # 确保嵌套实体类名称也以 Bean 结尾
                nested_class_name = nested_name
                if not nested_class_name.endswith("Bean"):
                    nested_class_name = nested_class_name + "Bean"
                
                lines.append("")
                lines.extend([
                    "/**",
                    f" * {nested_class_name}",
                    " */",
                    "@Parcelize",
                    f"data class {nested_class_name}("
                ])
                
                # 生成嵌套实体类的属性
                if nested_schema:
                    nested_properties = []
                    for key, value_info in nested_schema.items():
                        prop_type = value_info.get("type", "String")
                        nullable = value_info.get("nullable", False)
                        property_name = self._escape_kotlin_keyword(key)
                        
                        nested_property_code = f"    var {property_name}: {prop_type}{'?' if nullable else ''}"
                        nested_properties.append(nested_property_code)
                    
                    # 添加属性，最后一个不加逗号
                    for i, prop in enumerate(nested_properties):
                        if i < len(nested_properties) - 1:
                            lines.append(prop + ",")
                        else:
                            lines.append(prop)
                else:
                    lines.append("    // TODO: 根据实际响应数据添加属性")
                
                lines.append(") : Parcelable")
        
        return "\n".join(lines)
    
    def generate_request_entity(self, entity_name: str, params: Dict[str, Any]) -> str:
        """
        生成请求实体类代码
        
        Args:
            entity_name: 实体类名称
            params: 请求参数定义
        
        Returns:
            生成的 Kotlin 代码字符串
        """
        return self.generate_entity(f"{entity_name}Request", params)
    
    def generate_response_entity(self, entity_name: str, schema: Dict[str, Any]) -> str:
        """
        生成响应实体类代码
        
        Args:
            entity_name: 实体类名称
            schema: 响应数据结构定义
        
        Returns:
            生成的 Kotlin 代码字符串
        """
        return self.generate_entity(f"{entity_name}Response", schema)
    
    def _escape_kotlin_keyword(self, key: str) -> str:
        """转义 Kotlin 关键字"""
        kotlin_keywords = {
            "val", "var", "fun", "class", "object", "interface",
            "if", "else", "when", "for", "while", "do", "try", "catch",
            "return", "break", "continue", "null", "true", "false",
            "this", "super", "is", "as", "in", "out", "typealias"
        }
        
        if key in kotlin_keywords:
            return f"`{key}`"
        return key
    
    def generate_response_data_base_class(self) -> str:
        """
        生成通用的 ResponseData 基类
        
        Returns:
            生成的 Kotlin 代码字符串
        """
        lines = [
            f"package {self.base_package}.entities",
            "",
            "import android.os.Parcelable",
            "import kotlinx.parcelize.Parcelize",
            "",
            "/**",
            " * 通用响应数据包装类",
            " * 所有 API 响应都使用此包装格式",
            " * 自动生成的实体类",
            " * 由 ShowDoc 文档自动生成",
            " */",
            "@Parcelize",
            "data class ResponseData<out T : Parcelable>(",
            "    var code: Int,",
            "",
            "    var msg: String,",
            "",
            "    val data: T,",
            "",
            "    var hasNext: Int,",
            ") : Parcelable {",
            "    companion object {",
            "        const val REQUEST_CODE_SUCCESS = 1",
            "    }",
            "",
            "    val success: Boolean",
            "        get() = code == REQUEST_CODE_SUCCESS",
            "}",
        ]
        
        return "\n".join(lines)
    
    def _to_camel_case(self, text: str) -> str:
        """转换为驼峰命名"""
        import re
        words = re.sub(r'[^\w]', '_', text).split('_')
        result = ''.join(word.capitalize() if i > 0 else word.lower() 
                        for i, word in enumerate(words) if word)
        if not result:
            return text
        return result[0].lower() + result[1:] if len(result) > 1 else result.lower()
    
    def _extract_chinese_name(
        self, 
        api_data: Optional[Dict[str, Any]], 
        default_name: str
    ) -> str:
        """
        从 API 数据中提取中文名称
        
        Args:
            api_data: API 数据，包含 page 和 api 信息
            default_name: 默认名称（通常是英文类名）
        
        Returns:
            中文名称，如果无法提取则返回默认名称
        """
        if not api_data:
            return default_name
        
        # 优先从 page.page_title 获取
        page = api_data.get("page")
        if page and hasattr(page, 'page_title') and page.page_title:
            return page.page_title.strip()
        
        # 其次从 api.title 获取
        api = api_data.get("api")
        if api and hasattr(api, 'title') and api.title:
            return api.title.strip()
        
        # 如果都没有，返回默认名称
        return default_name
    
    def _build_document_url(
        self, 
        api_data: Optional[Dict[str, Any]], 
        item_id: Optional[str], 
        server_base: Optional[str]
    ) -> Optional[str]:
        """
        构建 ShowDoc 文档链接
        
        Args:
            api_data: API 数据，包含 page 信息
            item_id: ShowDoc 项目 ID
            server_base: ShowDoc 服务器地址
        
        Returns:
            文档链接 URL，如果无法构建则返回 None
        """
        if not api_data or not item_id or not server_base:
            return None
        
        page = api_data.get("page")
        if not page or not hasattr(page, 'page_id'):
            return None
        
        page_id = page.page_id
        if not page_id:
            return None
        
        # ShowDoc 文档 URL 格式：{server_base}/web/#/{item_id}/{page_id}
        return f"{server_base}/web/#/{item_id}/{page_id}"
    
    def _extract_response_example(self, api_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        从 API 数据中提取响应示例（JSON 字符串）
        
        Args:
            api_data: API 数据，包含 response 信息
        
        Returns:
            响应示例 JSON 字符串，如果无法提取则返回 None
        """
        if not api_data:
            return None
        
        # 优先从 page.raw_content 中获取完整的 response 数据
        page = api_data.get("page")
        response_data = None
        
        if page and hasattr(page, 'raw_content') and page.raw_content:
            response_data = page.raw_content.get("response")
        
        # 如果没有，使用 api.response
        api = api_data.get("api")
        if not response_data and api:
            response_data = api.response
        
        if not response_data:
            return None
        
        # 优先使用 responseExample（JSON 字符串）
        if "responseExample" in response_data:
            example = response_data["responseExample"]
            if example and isinstance(example, str) and example.strip():
                return example.strip()
        
        # 其次使用 responseOriginal（字典）
        if "responseOriginal" in response_data:
            original = response_data["responseOriginal"]
            if original:
                try:
                    # 转换为格式化的 JSON 字符串
                    return json.dumps(original, ensure_ascii=False, indent=2)
                except:
                    pass
        
        # 最后使用 responseText（JSON 字符串）
        if "responseText" in response_data:
            text = response_data["responseText"]
            if text and isinstance(text, str) and text.strip():
                return text.strip()
        
        return None
    
    def _format_json_for_comment(self, json_str: str) -> str:
        """
        格式化 JSON 字符串为注释格式（每行前面不加 *，因为会在调用处添加）
        
        Args:
            json_str: JSON 字符串
        
        Returns:
            格式化后的字符串（每行独立）
        """
        try:
            # 尝试解析并重新格式化 JSON（确保缩进正确）
            parsed = json.loads(json_str)
            formatted = json.dumps(parsed, ensure_ascii=False, indent=2)
            return formatted
        except:
            # 如果解析失败，返回原始字符串
            return json_str

