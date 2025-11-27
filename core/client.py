"""
ShowDoc 客户端主类
"""
import json
import re
import time
from typing import Optional, Dict, Any, List

import requests
from requests.adapters import HTTPAdapter
from requests.utils import cookiejar_from_dict
from urllib3.util.retry import Retry

from .exceptions import (
    ShowDocError,
    ShowDocAuthError,
    ShowDocNotFoundError,
    ShowDocParseError,
    ShowDocNetworkError,
    ShowDocCaptchaError,
)
from .parser import (
    parse_showdoc_url,
    decode_page_content,
    find_category_by_name,
    filter_categories_by_name,
    build_category_tree
)
from .captcha_solver import CaptchaSolver, CaptchaSolveResult
from .models import (
    ItemInfo,
    Category,
    Page,
    ApiDefinition,
    ApiTree
)


class ShowDocClient:
    """ShowDoc 客户端类，用于获取接口文档数据"""
    
    def __init__(self, base_url: str, cookie: Optional[str] = None, password: Optional[str] = "123456"):
        """
        初始化 ShowDoc 客户端
        
        Args:
            base_url: ShowDoc 文档页面 URL，例如 "https://doc.cqfengli.com/web/#/90/"
            cookie: 认证 Cookie，例如 "think_language=zh-CN; PHPSESSID=xxx"（可选）
            password: 项目访问密码，如果提供且 cookie 为空，将自动进行密码登录（默认: "123456"）
        """
        # 解析 URL，提取服务器地址和 item_id
        url_info = parse_showdoc_url(base_url)
        self.server_base = url_info["server_base"]
        self.item_id = url_info["item_id"]
        self.cookie = cookie
        
        # 初始化 HTTP session
        self.session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 设置默认请求头
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        
        # 如果提供了 Cookie，直接设置
        if cookie:
            self.session.headers["Cookie"] = cookie
        # 如果没有 Cookie 但提供了密码，自动进行密码登录
        elif password:
            self.authenticate_with_password(password)
            # 登录成功后，从 session 中提取 Cookie
            cookies_dict = self.session.cookies.get_dict()
            cookie_parts = []
            for key, value in cookies_dict.items():
                cookie_parts.append(f"{key}={value}")
            if cookie_parts:
                self.cookie = "; ".join(cookie_parts)
                self.session.headers["Cookie"] = self.cookie
        else:
            raise ShowDocAuthError("必须提供 cookie 或 password 之一进行认证")
    
    def _make_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> requests.Response:
        """
        发送 HTTP 请求（内部方法）
        
        Args:
            method: HTTP 方法（GET, POST）
            url: 请求 URL
            data: POST 数据
            timeout: 超时时间（秒）
        
        Returns:
            Response 对象
        
        Raises:
            ShowDocNetworkError: 网络请求失败
            ShowDocAuthError: 认证失败
        """
        try:
            if method.upper() == "GET":
                response = self.session.get(url, timeout=timeout)
            elif method.upper() == "POST":
                response = self.session.post(
                    url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=timeout
                )
            else:
                raise ShowDocNetworkError(f"不支持的 HTTP 方法: {method}")
            
            # 检查 HTTP 状态码
            if response.status_code == 401 or response.status_code == 403:
                raise ShowDocAuthError(f"认证失败: HTTP {response.status_code}")
            
            if response.status_code != 200:
                raise ShowDocNetworkError(
                    f"请求失败: HTTP {response.status_code}, URL: {url}"
                )
            
            return response
        
        except requests.exceptions.Timeout:
            raise ShowDocNetworkError(f"请求超时: {url}")
        except requests.exceptions.ConnectionError as e:
            raise ShowDocNetworkError(f"连接失败: {str(e)}")
        except (ShowDocAuthError, ShowDocNetworkError):
            raise
        except Exception as e:
            raise ShowDocNetworkError(f"请求异常: {str(e)}")
    
    def _parse_json_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        解析 JSON 响应
        
        Args:
            response: Response 对象
        
        Returns:
            解析后的 JSON 字典
        
        Raises:
            ShowDocParseError: JSON 解析失败
        """
        try:
            # 检查响应内容类型
            content_type = response.headers.get("Content-Type", "").lower()
            
            # 先尝试直接解析为 JSON
            try:
                return response.json()
            except (json.JSONDecodeError, ValueError):
                pass
            
            # 如果直接解析失败，尝试从文本中提取 JSON
            text = response.text.strip()
            
            # 尝试找到 JSON 对象的开始和结束
            # 查找第一个 { 和最后一个 }
            start_idx = text.find('{')
            if start_idx == -1:
                raise ShowDocParseError("响应中未找到 JSON 对象")
            
            # 从后往前找最后一个 }
            end_idx = text.rfind('}')
            if end_idx == -1 or end_idx <= start_idx:
                raise ShowDocParseError("响应中未找到完整的 JSON 对象")
            
            json_str = text[start_idx:end_idx + 1]
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            raise ShowDocParseError(f"JSON 解析失败: {str(e)}")
        except Exception as e:
            raise ShowDocParseError(f"解析响应失败: {str(e)}")
    
    def authenticate_with_password(self, password: str, max_attempts: int = 5) -> None:
        """
        使用密码和验证码进行自动登录
        
        Args:
            password: 项目访问密码
            max_attempts: 最大重试次数（验证码识别失败时）
        
        Raises:
            ShowDocAuthError: 登录失败（密码错误或达到最大重试次数）
            ShowDocCaptchaError: 验证码识别失败
        """
        from .parser import ERROR_CODE_PASSWORD_REQUIRED, ERROR_CODE_CAPTCHA_INCORRECT
        
        captcha_solver = CaptchaSolver()
        
        for attempt in range(max_attempts):
            try:
                # 步骤 1: 创建验证码
                create_captcha_url = f"{self.server_base}/server/index.php?s=/api/common/createCaptcha"
                create_response = self._make_request("POST", create_captcha_url, data={})
                create_result = self._parse_json_response(create_response)
                
                if create_result.get("error_code") != 0:
                    raise ShowDocAuthError(f"创建验证码失败: {create_result.get('error_message', '未知错误')}")
                
                captcha_id = create_result.get("data", {}).get("captcha_id")
                if not captcha_id:
                    raise ShowDocAuthError("创建验证码返回数据无效")
                
                # 步骤 2: 获取验证码图片
                show_captcha_url = f"{self.server_base}/server/index.php?s=/api/common/showCaptcha&captcha_id={captcha_id}&{int(time.time() * 1000)}"
                captcha_response = self._make_request("GET", show_captcha_url)
                
                if captcha_response.headers.get("Content-Type", "").startswith("image/"):
                    captcha_image_bytes = captcha_response.content
                else:
                    raise ShowDocAuthError("获取验证码图片失败")
                
                # 步骤 3: 识别验证码
                try:
                    solve_result = captcha_solver.solve(captcha_image_bytes)
                    captcha_text = solve_result.text
                except ShowDocCaptchaError as e:
                    if attempt < max_attempts - 1:
                        # 验证码识别失败，重试
                        time.sleep(0.5)  # 短暂延迟后重试
                        continue
                    else:
                        raise ShowDocAuthError(f"验证码识别失败（已重试 {max_attempts} 次）: {str(e)}")
                
                # 步骤 4: 提交密码和验证码
                # 注意：page_id 可以从 URL 中提取，如果没有则使用 item_id
                # 根据示例，page_id 可能是可选的，先尝试使用 item_id
                pwd_url = f"{self.server_base}/server/index.php?s=/api/item/pwd"
                pwd_data = {
                    "item_id": self.item_id,
                    "password": password,
                    "captcha": captcha_text,
                    "captcha_id": captcha_id,
                }
                
                pwd_response = self._make_request("POST", pwd_url, data=pwd_data)
                pwd_result = self._parse_json_response(pwd_response)
                
                error_code = pwd_result.get("error_code")
                
                # 登录成功
                if error_code == 0:
                    # 登录成功，session 会自动保存 Cookie
                    return
                
                # 验证码错误，重试
                elif error_code == ERROR_CODE_CAPTCHA_INCORRECT:
                    if attempt < max_attempts - 1:
                        time.sleep(0.5)
                        continue
                    else:
                        raise ShowDocAuthError(f"验证码错误（已重试 {max_attempts} 次）")
                
                # 密码错误或其他认证错误
                elif error_code == ERROR_CODE_PASSWORD_REQUIRED or error_code in (10201, 10202, 10203, 10204, 10205):
                    error_msg = pwd_result.get("error_message", "密码错误")
                    raise ShowDocAuthError(f"密码错误: {error_msg}")
                
                # 其他错误
                else:
                    error_msg = pwd_result.get("error_message", "未知错误")
                    raise ShowDocAuthError(f"登录失败 (error_code={error_code}): {error_msg}")
            
            except (ShowDocAuthError, ShowDocCaptchaError):
                raise
            except Exception as e:
                if attempt < max_attempts - 1:
                    time.sleep(0.5)
                    continue
                else:
                    raise ShowDocAuthError(f"登录过程发生异常（已重试 {max_attempts} 次）: {str(e)}")
        
        raise ShowDocAuthError(f"登录失败：已达到最大重试次数 ({max_attempts})")
    
    def fetch_homepage(self) -> Dict[str, Any]:
        """
        访问主页面获取配置信息
        
        Returns:
            包含配置信息的字典
        """
        url = f"{self.server_base}/web/"
        response = self._make_request("GET", url)
        
        # 主页面返回的是 HTML，从中提取配置
        html_content = response.text
        
        # 从 HTML 中提取 DocConfig（如果存在）
        config_match = re.search(r'window\.DocConfig\s*=\s*({[^}]+})', html_content)
        if config_match:
            try:
                config = json.loads(config_match.group(1))
                return {"config": config}
            except:
                pass
        
        return {"html": html_content}
    
    def fetch_item_info(self, item_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取文档目录结构
        
        Args:
            item_id: 项目 ID，如果为 None 则使用初始化时的 item_id
        
        Returns:
            完整的目录树结构（JSON 格式）
        """
        if item_id is None:
            item_id = self.item_id
        
        url = f"{self.server_base}/server/index.php?s=/api/item/info"
        data = {"item_id": item_id}
        
        response = self._make_request("POST", url, data=data)
        result = self._parse_json_response(response)
        
        # 检查错误码
        if result.get("error_code") != 0:
            error_msg = result.get("error_msg", "未知错误")
            raise ShowDocError(f"获取目录结构失败: {error_msg}")
        
        return result.get("data", {})
    
    def fetch_ai_config(self, item_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取 AI 知识库配置（可选）
        
        Args:
            item_id: 项目 ID，如果为 None 则使用初始化时的 item_id
        
        Returns:
            AI 配置信息
        """
        if item_id is None:
            item_id = self.item_id
        
        url = f"{self.server_base}/server/index.php?s=/api/item/getAiKnowledgeBaseConfig"
        data = {"item_id": item_id}
        
        try:
            response = self._make_request("POST", url, data=data)
            result = self._parse_json_response(response)
            
            if result.get("error_code") == 0:
                return result.get("data", {})
            return {}
        except Exception:
            # AI 配置是可选的，失败时返回空字典
            return {}
    
    def fetch_page_info(self, page_id: str) -> Dict[str, Any]:
        """
        获取单个页面的详细信息
        
        Args:
            page_id: 页面 ID
        
        Returns:
            包含 API 定义的页面数据
        
        Raises:
            ShowDocNotFoundError: 页面不存在
        """
        url = f"{self.server_base}/server/index.php?s=/api/page/info"
        data = {"page_id": page_id}
        
        response = self._make_request("POST", url, data=data)
        result = self._parse_json_response(response)
        
        # 检查错误码
        if result.get("error_code") != 0:
            error_msg = result.get("error_msg", "页面不存在")
            raise ShowDocNotFoundError(f"获取页面信息失败: {error_msg}")
        
        page_data = result.get("data", {})
        
        # 处理 page_content（HTML 实体解码）
        if "page_content" in page_data:
            encoded_content = page_data["page_content"]
            try:
                decoded_content = decode_page_content(encoded_content)
                page_data["decoded_content"] = decoded_content
            except ShowDocParseError:
                # 解码失败时保留原始数据
                pass
        
        return page_data
    
    def _parse_api_definition(self, page_data: Dict[str, Any]) -> Optional[ApiDefinition]:
        """
        从页面数据中解析 API 定义
        
        Args:
            page_data: 页面数据字典
        
        Returns:
            ApiDefinition 对象，如果不是 API 页面则返回 None
        """
        decoded_content = page_data.get("decoded_content")
        if not decoded_content:
            return None
        
        info = decoded_content.get("info", {})
        if info.get("type") != "api":
            return None
        
        request_data = decoded_content.get("request", {})
        response_data = decoded_content.get("response", {})
        
        return ApiDefinition(
            method=info.get("method", "GET").upper(),
            url=info.get("url", ""),
            title=info.get("title", ""),
            description=info.get("description", ""),
            request=request_data,
            response=response_data,
            headers=request_data.get("headers"),
            query=request_data.get("query"),
            body=request_data.get("params")
        )
    
    def _build_category_from_dict(
        self,
        cat_dict: Dict[str, Any],
        item_id: str,
        fetch_details: bool = True
    ) -> Category:
        """
        从字典数据构建 Category 对象
        
        Args:
            cat_dict: 分类字典数据
            item_id: 项目 ID
            fetch_details: 是否获取页面详情
        
        Returns:
            Category 对象
        """
        cat_id = str(cat_dict.get("cat_id", ""))
        
        # 构建页面列表
        pages = []
        page_list = cat_dict.get("pages", [])
        for page_dict in page_list:
            page_id = str(page_dict.get("page_id", ""))
            
            # 获取页面详情（如果需要）
            api_info = None
            raw_content = None
            if fetch_details and page_id:
                try:
                    page_data = self.fetch_page_info(page_id)
                    raw_content = page_data.get("decoded_content")
                    api_info = self._parse_api_definition(page_data)
                except Exception as e:
                    # 获取页面详情失败时记录错误，但不中断流程
                    print(f"警告: 获取页面 {page_id} 详情失败: {str(e)}")
            
            page = Page(
                page_id=page_id,
                page_title=page_dict.get("page_title", ""),
                cat_id=cat_id,
                author_uid=str(page_dict.get("author_uid", "")),
                author_username=page_dict.get("author_username", ""),
                api_info=api_info,
                ext_info=page_dict.get("ext_info"),
                raw_content=raw_content
            )
            pages.append(page)
        
        # 递归构建子分类
        children = []
        sub_catalogs = cat_dict.get("catalogs", [])
        for sub_cat_dict in sub_catalogs:
            child_cat = self._build_category_from_dict(
                sub_cat_dict, item_id, fetch_details
            )
            children.append(child_cat)
        
        return Category(
            cat_id=cat_id,
            cat_name=cat_dict.get("cat_name", ""),
            item_id=item_id,
            parent_cat_id=str(cat_dict.get("parent_cat_id", "")),
            level=int(cat_dict.get("level", 0)),
            s_number=str(cat_dict.get("s_number", "")),
            pages=pages,
            children=children
        )
    
    def _filter_categories_recursive(
        self,
        categories: List[Dict[str, Any]],
        node_name: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        递归筛选分类节点
        
        Args:
            categories: 分类列表
            node_name: 节点名称，None/"全部"/"all" 表示返回所有
        
        Returns:
            筛选后的分类列表
        """
        if not node_name or node_name.strip().lower() in ("全部", "all"):
            return categories
        
        node_name = node_name.strip()
        
        def search_and_collect(cat_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            result = []
            for cat in cat_list:
                cat_name = cat.get("cat_name", "")
                if cat_name == node_name:
                    # 找到匹配的节点，返回该节点及其所有子节点
                    result.append(cat)
                else:
                    # 递归搜索子分类
                    sub_catalogs = cat.get("catalogs", [])
                    if sub_catalogs:
                        matched = search_and_collect(sub_catalogs)
                        if matched:
                            result.extend(matched)
            return result
        
        return search_and_collect(categories)
    
    def get_all_apis(self, node_name: Optional[str] = None) -> ApiTree:
        """
        获取所有接口数据（主入口方法）
        
        Args:
            node_name: 节点名称，例如 "订单"
                       - None/"全部"/"all": 获取所有节点
                       - 具体名称: 只获取该节点及其子节点的数据
        
        Returns:
            ApiTree 对象，包含完整的接口树结构
        
        Raises:
            ShowDocNotFoundError: 指定的节点不存在
        """
        # 步骤1: 访问主页面（可选，主要为了确保连接正常）
        try:
            self.fetch_homepage()
        except Exception:
            pass  # 忽略主页面访问失败
        
        # 步骤2: 获取目录结构
        item_data = self.fetch_item_info()
        
        # 提取项目信息
        item_info = ItemInfo(
            item_id=str(item_data.get("item_id", self.item_id)),
            item_name=item_data.get("item_name", ""),
            item_domain=item_data.get("item_domain", ""),
            is_archived=item_data.get("is_archived", "0"),
            default_page_id=item_data.get("default_page_id"),
            default_cat_id2=item_data.get("default_cat_id2"),
            default_cat_id3=item_data.get("default_cat_id3"),
            default_cat_id4=item_data.get("default_cat_id4"),
        )
        
        # 步骤3: 获取目录树
        menu = item_data.get("menu", {})
        all_catalogs = build_category_tree(menu, item_info.item_id)
        
        # 处理根级别的页面（cat_id 为 "0"）
        root_pages_data = menu.get("pages", [])
        root_category = None
        if root_pages_data:
            root_category = {
                "cat_id": "0",
                "cat_name": "根目录",
                "parent_cat_id": "0",
                "level": 0,
                "pages": root_pages_data,
                "catalogs": []
            }
            all_catalogs.insert(0, root_category)
        
        # 步骤4: 筛选节点
        if node_name and node_name.strip().lower() not in ("全部", "all"):
            filtered_catalogs = self._filter_categories_recursive(
                all_catalogs, node_name.strip()
            )
            if not filtered_catalogs:
                raise ShowDocNotFoundError(f"未找到名称为 '{node_name}' 的节点")
        else:
            filtered_catalogs = all_catalogs
        
        # 步骤5: 构建完整的树结构（包括页面详情）
        categories = []
        for cat_dict in filtered_catalogs:
            category = self._build_category_from_dict(
                cat_dict, item_info.item_id, fetch_details=True
            )
            categories.append(category)
        
        # 构建 ApiTree 对象
        api_tree = ApiTree(
            item_info=item_info,
            categories=categories
        )
        
        return api_tree

