"""
Flutter 代码生成器主类

整合各个代码生成器，提供统一的接口来生成完整的 Flutter 项目代码
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import os
import hashlib

from core.models import ApiTree, ApiDefinition, Page, Category

from .dio_service_generator import DioServiceGenerator
from .entity_generator import FlutterEntityGenerator
from .dio_config import DioConfigGenerator
from .repository_generator import FlutterRepositoryGenerator
from .entity_schema import (
    extract_data_from_response,
    extract_data_from_request,
    analyze_entity_schema,
    sanitize_category_name
)
from .version_control import FlutterVersionControlManager


def _calculate_content_hash(content: str) -> str:
    """计算内容哈希值"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()


class FlutterCodeGenerator:
    """Flutter 代码生成器，负责生成完整的 Flutter 项目代码"""
    
    def __init__(
        self,
        base_package: str = "com.example.api",
        output_dir: str = "flutter_output"
    ):
        """
        初始化代码生成器
        
        Args:
            base_package: Flutter 项目的基础包名
            output_dir: 输出目录
        """
        self.base_package = base_package
        self.output_dir = Path(output_dir)
        self.dio_gen = DioServiceGenerator(base_package)
        self.entity_gen = FlutterEntityGenerator(base_package)
        self.dio_config_gen = DioConfigGenerator(base_package)
        self.repository_gen = FlutterRepositoryGenerator(base_package)
        
        # 创建输出目录结构
        self._create_output_dirs()
    
    def _create_output_dirs(self):
        """创建输出目录结构"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "services").mkdir(exist_ok=True)
        (self.output_dir / "models").mkdir(exist_ok=True)
        (self.output_dir / "repositories").mkdir(exist_ok=True)
        (self.output_dir / "config").mkdir(exist_ok=True)
    
    def generate(
        self, 
        api_tree: ApiTree, 
        category_filter: Optional[str] = None,
        server_base: Optional[str] = None,
        enable_version_control: bool = True,
        auto_delete_orphaned: bool = False,
    ) -> Dict[str, List[str]]:
        """
        生成完整的 Flutter 代码
        
        Args:
            api_tree: 从 core 模块获取的 API 树结构
            category_filter: 可选的分类名称过滤器
            server_base: ShowDoc 服务器地址（用于生成文档链接），例如 "https://doc.cqfengli.com"
            enable_version_control: 是否启用版本控制（增量更新）
            auto_delete_orphaned: 是否自动删除已孤立的旧文件（默认 False：只标记不删除）
        
        Returns:
            包含生成文件路径的字典，以及版本控制信息
        """
        # 初始化版本控制管理器
        vc_manager = None
        if enable_version_control:
            vc_manager = FlutterVersionControlManager(self.output_dir)
        
        generated_files = {
            "services": [],
            "models": [],
            "repositories": [],
            "config": []
        }
        
        # 保存 item_id 和 server_base 用于生成文档链接
        self.item_id = api_tree.item_info.item_id
        self.server_base = server_base
        
        # 收集所有 API 定义
        all_apis = self._collect_all_apis(api_tree, category_filter)
        
        # 去重：相同的 API URL + Method 只保留一个
        all_apis = self._deduplicate_apis(all_apis)
        
        # 收集当前所有 API 的键（用于检测已删除的 API）
        current_api_keys = set()
        for api_data in all_apis:
            api = api_data["api"]
            current_api_keys.add((api.url or "", api.method or ""))
        
        # 收集所有响应实体类型和请求实体类型（包含嵌套实体）
        all_entities, response_entity_mapping, request_entity_mapping = self._collect_entity_types(all_apis)
        
        # 保存实体类集合，供 Dio 和 Repository 生成器使用
        self.available_entities = set(entity_name for entity_name in all_entities.keys())
        
        # 保存 API 到实体类名称的映射
        self.api_to_response_entity = {}
        self.api_to_request_entity = {}
        for api_data in all_apis:
            api = api_data["api"]
            key = (api.url or "", api.method or "")
            api_id = id(api_data)
            if api_id in response_entity_mapping:
                self.api_to_response_entity[key] = response_entity_mapping[api_id]
            if api_id in request_entity_mapping:
                self.api_to_request_entity[key] = request_entity_mapping[api_id]
        
        # 步骤1: 预生成所有代码内容并计算哈希值
        file_contents = {}  # {relative_path: (content, api_key)}
        
        # 生成 Dio Service 接口
        service_code = self.dio_gen.generate_services(
            all_apis, 
            available_entities=self.available_entities,
            api_to_response_entity=self.api_to_response_entity,
            api_to_request_entity=self.api_to_request_entity
        )
        file_contents["services/api_service.dart"] = (service_code, None)
        
        # 生成 Repository 类
        repository_code = self.repository_gen.generate_repository(
            all_apis, 
            available_entities=self.available_entities,
            api_to_response_entity=self.api_to_response_entity,
            api_to_request_entity=self.api_to_request_entity
        )
        file_contents["repositories/api_repository.dart"] = (repository_code, None)
        
        # 生成通用的 ResponseData 基类（放在 models 根目录）
        response_data_code = self.entity_gen.generate_response_data_base_class()
        file_contents["models/response_data.dart"] = (response_data_code, None)
        
        # 按分类组织实体类
        entities_by_category = self._organize_entities_by_category(all_entities, all_apis)
        
        # 为每个分类生成实体类，按 request/response 区分
        for category_name, category_entities in entities_by_category.items():
            # 创建分类文件夹
            category_package = sanitize_category_name(category_name)
            
            # 生成该分类下的所有实体类（包含嵌套实体类，放在同一个文件中）
            for entity_info in category_entities:
                entity_name = entity_info["name"]
                entity_schema = entity_info["schema"]
                nested_entities = entity_info.get("nested", {})
                
                # 判断是 Request 还是 Response
                is_request = entity_name.endswith("Request")
                entity_type = "request" if is_request else "response"
                
                # 获取 api_data 用于生成文档链接和响应示例和关联 API
                api_data = entity_info.get("api_data")
                api_key = None
                if api_data:
                    api = api_data.get("api")
                    if api:
                        api_key = (api.url or "", api.method or "")
                
                # 生成主实体类（包含嵌套实体类）
                entity_code = self.entity_gen.generate_entity(
                    entity_name, 
                    entity_schema,
                    category_name,
                    nested_entities,
                    entity_type,
                    api_data,
                    self.item_id,
                    self.server_base
                )
                
                # 构建相对路径
                relative_path = f"models/{category_package}/{entity_type}/{entity_name.lower()}.dart"
                file_contents[relative_path] = (entity_code, api_key)
        
        # 生成 Dio 配置
        dio_code = self.dio_config_gen.generate_config()
        file_contents["config/dio_config.dart"] = (dio_code, None)
        
        # 生成依赖配置（pubspec.yaml）
        pubspec_code = self._generate_pubspec_dependencies()
        file_contents["pubspec_dependencies.yaml"] = (pubspec_code, None)
        
        # 步骤2: 版本控制比较和增量更新
        vc_info = {}
        new_file_hashes = {}
        
        if enable_version_control and vc_manager:
            # 计算所有新文件的哈希值
            for relative_path, (content, api_key) in file_contents.items():
                content_hash = _calculate_content_hash(content)
                new_file_hashes[relative_path] = content_hash
            
            # 比较文件，获取需要更新的文件列表
            to_update, to_delete, unchanged = vc_manager.compare_files(new_file_hashes)
            
            # 检测孤立的 API 文件（接口文档中已不存在）
            orphaned_files = vc_manager.get_orphaned_api_files(current_api_keys)
            
            # 保存统计信息
            vc_info = {
                "updated": len(to_update),
                "unchanged": len(unchanged),
                "to_delete": len(to_delete),
                "orphaned": len(orphaned_files),
                "orphaned_files": orphaned_files,
                "to_delete_files": list(to_delete)
            }

            # 根据参数决定是否自动清理孤立文件和待删除文件
            if auto_delete_orphaned:
                if orphaned_files:
                    vc_manager.clean_orphaned_files(orphaned_files, delete_files=True)
                if to_delete:
                    vc_manager.clean_orphaned_files(list(to_delete), delete_files=True)
            
            # 只写入需要更新的文件
            files_to_write = list(to_update)
            files_existing = list(unchanged)
        else:
            # 如果未启用版本控制，写入所有文件
            files_to_write = list(file_contents.keys())
            files_existing = []
            vc_info = {
                "updated": len(files_to_write),
                "unchanged": 0,
                "to_delete": 0,
                "orphaned": 0,
                "orphaned_files": [],
                "to_delete_files": []
            }
        
        # 步骤3: 写入文件
        for relative_path in files_to_write:
            content, api_key = file_contents[relative_path]
            full_path = self.output_dir / relative_path
            
            # 确保目录存在
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            full_path.write_text(content, encoding="utf-8")
            
            # 添加到生成文件列表
            if relative_path.startswith("services/"):
                generated_files["services"].append(str(full_path))
            elif relative_path.startswith("models/"):
                generated_files["models"].append(str(full_path))
            elif relative_path.startswith("repositories/"):
                generated_files["repositories"].append(str(full_path))
            elif relative_path.startswith("config/") or relative_path.endswith(".yaml"):
                generated_files["config"].append(str(full_path))
            
            # 记录到版本控制
            if enable_version_control and vc_manager:
                content_hash = _calculate_content_hash(content)
                vc_manager.record_file(relative_path, content_hash, api_key)
        
        # 添加未变化的文件到生成文件列表
        for relative_path in files_existing:
            full_path = self.output_dir / relative_path
            if full_path.exists():
                if relative_path.startswith("services/"):
                    generated_files["services"].append(str(full_path))
                elif relative_path.startswith("models/"):
                    generated_files["models"].append(str(full_path))
                elif relative_path.startswith("repositories/"):
                    generated_files["repositories"].append(str(full_path))
                elif relative_path.startswith("config/") or relative_path.endswith(".yaml"):
                    generated_files["config"].append(str(full_path))
                
                # 更新文件索引中的时间戳
                if enable_version_control and vc_manager:
                    content_hash = new_file_hashes.get(relative_path)
                    _, api_key = file_contents.get(relative_path, (None, None))
                    if content_hash:
                        vc_manager.record_file(relative_path, content_hash, api_key)
        
        # 步骤4: 提交版本控制更改
        if enable_version_control and vc_manager:
            vc_manager.commit()
        
        # 添加版本控制信息到返回值
        generated_files["version_control"] = vc_info
        
        return generated_files
    
    def _collect_all_apis(
        self,
        api_tree: ApiTree,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """收集所有 API 定义"""
        apis = []
        
        def collect_from_category(category: Category):
            for page in category.pages:
                if page.api_info:
                    apis.append({
                        "api": page.api_info,
                        "page": page,
                        "category": category
                    })
            
            for child in category.children:
                collect_from_category(child)
        
        categories = api_tree.categories
        if category_filter:
            categories = [
                cat for cat in categories
                if category_filter.lower() in cat.cat_name.lower()
            ]
        
        for category in categories:
            collect_from_category(category)
        
        return apis
    
    def _deduplicate_apis(self, apis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重 API：相同的 URL + Method 只保留第一个"""
        seen = {}
        unique_apis = []
        
        for api_data in apis:
            api = api_data["api"]
            key = f"{api.method.upper()}:{api.url}"
            
            if key not in seen:
                seen[key] = True
                unique_apis.append(api_data)
        
        return unique_apis
    
    def _collect_entity_types(self, apis: List[Dict[str, Any]]) -> tuple:
        """
        收集所有响应实体类型和请求实体类型定义（包含嵌套实体）
        
        Returns:
            (entities_dict, response_entity_mapping, request_entity_mapping)
        """
        # 第一步：收集所有需要生成响应实体类的 API，并解决名称冲突
        response_entity_mapping = self._resolve_entity_name_conflicts(apis, "response")
        
        # 第二步：收集所有需要生成请求实体类的 API，并解决名称冲突
        request_entity_mapping = self._resolve_entity_name_conflicts(apis, "request")
        
        # 第三步：使用解决冲突后的名称真正收集实体类定义
        entities = {}
        
        for api_data in apis:
            api = api_data["api"]
            category = api_data.get("category")
            category_name = category.cat_name if category else "默认"
            
            # 收集响应实体类型
            page = api_data.get("page")
            response_data = None
            
            if page and page.raw_content:
                response_data = page.raw_content.get("response")
            
            if not response_data:
                response_data = api.response
            
            if response_data:
                data_content = extract_data_from_response(response_data)
                
                if data_content is not None:
                    is_empty = False
                    if isinstance(data_content, dict) and not data_content:
                        is_empty = True
                    elif isinstance(data_content, list) and not data_content:
                        is_empty = True
                    elif isinstance(data_content, str) and not data_content.strip():
                        is_empty = True
                    
                    if not is_empty:
                        entity_name = response_entity_mapping.get(id(api_data))
                        if entity_name:
                            analyzed = analyze_entity_schema(data_content, entity_name)
                            
                            if analyzed.get("schema"):
                                entities[entity_name] = {
                                    "schema": analyzed["schema"],
                                    "nested": analyzed["nested"],
                                    "category": category_name,
                                    "api_data": api_data
                                }
            
            # 收集请求实体类型
            if api.body:
                request_data = extract_data_from_request(api.body)
                
                if request_data and isinstance(request_data, dict):
                    entity_name = request_entity_mapping.get(id(api_data))
                    if entity_name:
                        if "__param_list__" in request_data:
                            from .entity_schema import build_request_schema_from_params_dart
                            param_list = request_data["__param_list__"]
                            schema = build_request_schema_from_params_dart(param_list)
                            
                            entities[entity_name] = {
                                "schema": schema,
                                "nested": {},
                                "category": category_name,
                                "api_data": api_data
                            }
                        else:
                            analyzed = analyze_entity_schema(request_data, entity_name)
                            
                            entities[entity_name] = {
                                "schema": analyzed["schema"],
                                "nested": analyzed["nested"],
                                "category": category_name,
                                "api_data": api_data
                            }
        
        return entities, response_entity_mapping, request_entity_mapping
    
    def _resolve_entity_name_conflicts(self, apis: List[Dict[str, Any]], entity_type: str) -> Dict[int, str]:
        """
        解决实体类名称冲突
        
        Args:
            apis: API 列表
            entity_type: "request" 或 "response"
        
        Returns:
            映射表：api_data 的 id -> 最终实体类名称
        """
        from .utils import url_path_to_class_name, sanitize_class_name
        
        # 收集所有需要生成实体类的 API
        candidate_apis = []
        for api_data in apis:
            api = api_data["api"]
            
            if entity_type == "response":
                page = api_data.get("page")
                response_data = None
                
                if page and page.raw_content:
                    response_data = page.raw_content.get("response")
                
                if not response_data:
                    response_data = api.response
                
                if response_data:
                    data_content = extract_data_from_response(response_data)
                    
                    if data_content is not None:
                        is_empty = False
                        if isinstance(data_content, dict) and not data_content:
                            is_empty = True
                        elif isinstance(data_content, list) and not data_content:
                            is_empty = True
                        elif isinstance(data_content, str) and not data_content.strip():
                            is_empty = True
                        
                        if not is_empty:
                            candidate_apis.append(api_data)
            
            elif entity_type == "request":
                if api.body:
                    request_data = extract_data_from_request(api.body)
                    if request_data and isinstance(request_data, dict):
                        candidate_apis.append(api_data)
        
        # 为每个 API 生成实体类名称，解决冲突
        entity_mapping = {}
        name_usage = {}
        
        # 第一轮：使用 depth=1 生成初始名称
        for api_data in candidate_apis:
            api = api_data["api"]
            url = api.url or ""
            entity_name = None
            
            if url:
                class_name = url_path_to_class_name(url, "", depth=1)
                if class_name and class_name != "Api":
                    entity_name = class_name
            
            if not entity_name:
                page = api_data.get("page")
                api_obj = api_data["api"]
                title = api_obj.title or ""
                if page and hasattr(page, 'page_title'):
                    title = page.page_title or title
                
                if title:
                    title = title.replace("-克隆", "").replace("-副本", "").replace("-复制", "")
                    title = title.replace("API", "").replace("接口", "").strip()
                    class_name = sanitize_class_name(title)
                    if entity_type == "response":
                        if class_name.endswith("Response"):
                            class_name = class_name[:-8]
                    elif entity_type == "request":
                        if not class_name.endswith("Request"):
                            class_name += "Request"
                    
                    if class_name:
                        entity_name = class_name
            
            if not entity_name:
                entity_name = "Data" if entity_type == "response" else "Request"
            
            entity_mapping[id(api_data)] = entity_name
            
            if entity_name not in name_usage:
                name_usage[entity_name] = []
            name_usage[entity_name].append(api_data)
        
        # 解决冲突：对于使用相同名称的多个 API，逐步增加 depth
        for entity_name, api_list in name_usage.items():
            if len(api_list) > 1:
                for api_data in api_list:
                    api = api_data["api"]
                    url = api.url or ""
                    
                    if not url:
                        new_name = entity_name + str(api_list.index(api_data) + 1)
                        entity_mapping[id(api_data)] = new_name
                        continue
                    
                    max_depth = 5
                    for depth in range(2, max_depth + 1):
                        new_class_name = url_path_to_class_name(url, "", depth=depth)
                        if new_class_name and new_class_name != "Api":
                            new_entity_name = new_class_name
                            
                            conflict = False
                            for other_api_data in api_list:
                                if other_api_data != api_data:
                                    other_url = other_api_data["api"].url or ""
                                    if other_url:
                                        other_class_name = url_path_to_class_name(other_url, "", depth=depth)
                                        if other_class_name and other_class_name != "Api":
                                            if other_class_name == new_class_name:
                                                conflict = True
                                                break
                            
                            if not conflict:
                                entity_mapping[id(api_data)] = new_entity_name
                                break
                    else:
                        new_name = entity_name + str(api_list.index(api_data) + 1)
                        entity_mapping[id(api_data)] = new_name
        
        return entity_mapping
    
    def _organize_entities_by_category(
        self,
        all_entities: Dict[str, Dict[str, Any]],
        all_apis: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """按分类组织实体类"""
        entities_by_category = {}
        
        for entity_name, entity_info in all_entities.items():
            category_name = entity_info.get("category", "默认")
            
            if category_name not in entities_by_category:
                entities_by_category[category_name] = []
            
            entities_by_category[category_name].append({
                "name": entity_name,
                "schema": entity_info["schema"],
                "nested": entity_info.get("nested", {}),
                "api_data": entity_info.get("api_data")
            })
        
        return entities_by_category
    
    def _generate_pubspec_dependencies(self) -> str:
        """生成 pubspec.yaml 依赖配置"""
        lines = [
            "# 自动生成的依赖配置",
            "# 由 ShowDoc 文档自动生成",
            "# 请将以下依赖添加到你的 pubspec.yaml 文件中",
            "",
            "dependencies:",
            "  # Dio 网络库",
            "  dio: ^5.4.0",
            "",
            "  # JSON 序列化",
            "  json_annotation: ^4.8.1",
            "",
            "dev_dependencies:",
            "  # JSON 序列化代码生成",
            "  build_runner: ^2.4.7",
            "  json_serializable: ^6.7.1",
            "",
            "# 使用说明：",
            "# 1. 将上述依赖添加到你的 pubspec.yaml",
            "# 2. 运行 flutter pub get",
            "# 3. 运行 flutter pub run build_runner build 生成 .g.dart 文件",
        ]
        
        return "\n".join(lines)

