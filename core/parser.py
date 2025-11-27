"""
URL 解析和数据解析工具函数
"""
import re
import json
import html
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs

from .exceptions import ShowDocParseError

# ShowDoc API 错误码常量
ERROR_CODE_SUCCESS = 0
ERROR_CODE_PASSWORD_REQUIRED = 10303  # 不是项目创建者（需要密码）
ERROR_CODE_CAPTCHA_INCORRECT = 10206  # 验证码不正确


def parse_showdoc_url(url: str) -> Dict[str, str]:
    """
    从 ShowDoc URL 中提取服务器地址和 item_id
    
    Args:
        url: ShowDoc 文档 URL，例如 "https://doc.cqfengli.com/web/#/90/"
    
    Returns:
        包含 server_base 和 item_id 的字典
    
    Raises:
        ShowDocParseError: URL 格式不正确
    """
    try:
        parsed = urlparse(url)
        server_base = f"{parsed.scheme}://{parsed.netloc}"
        
        # 从 URL 中提取 item_id
        # 可能的位置：
        # 1. 哈希路径：/web/#/90/ -> 90
        # 2. 查询参数：?item_id=90
        # 3. 路径参数：/web/90/
        
        item_id = None
        
        # 尝试从哈希路径提取
        if parsed.fragment:
            # 哈希格式可能是 #/90/ 或 #/item/90 或直接是数字
            # 示例: #/90/ 或 #/item/90 或 90
            fragment = parsed.fragment
            # 先尝试匹配 #/90/ 格式
            match = re.search(r'^/?(\d+)', fragment)
            if match:
                item_id = match.group(1)
        
        # 尝试从查询参数提取
        if not item_id:
            query_params = parse_qs(parsed.query)
            if 'item_id' in query_params:
                item_id = query_params['item_id'][0]
        
        # 尝试从路径中提取
        if not item_id:
            path_match = re.search(r'/(\d+)/?$', parsed.path)
            if path_match:
                item_id = path_match.group(1)
        
        if not item_id:
            raise ShowDocParseError(f"无法从 URL 中提取 item_id: {url}")
        
        page_id_match = re.search(r'page_id=(\d+)', url)
        page_id = page_id_match.group(1) if page_id_match else None
        
        return {
            "server_base": server_base,
            "item_id": item_id,
            "page_id": page_id or ""
        }
    except Exception as e:
        raise ShowDocParseError(f"解析 URL 失败: {str(e)}") from e


def extract_item_id_from_url(url: str) -> str:
    """
    从 URL 中提取 item_id（便捷函数）
    
    Args:
        url: ShowDoc 文档 URL
    
    Returns:
        item_id 字符串
    """
    result = parse_showdoc_url(url)
    return result["item_id"]


def decode_page_content(encoded_content: str) -> Dict[str, Any]:
    """
    HTML 实体解码并解析 JSON
    
    Args:
        encoded_content: 经过 HTML 实体编码的 JSON 字符串
    
    Returns:
        解析后的 JSON 对象（字典）
    
    Raises:
        ShowDocParseError: 解码或解析失败
    """
    try:
        # 1. HTML 实体解码
        decoded_content = html.unescape(encoded_content)
        
        # 2. 解析为 JSON 对象
        page_content = json.loads(decoded_content)
        
        return page_content
    except json.JSONDecodeError as e:
        raise ShowDocParseError(f"JSON 解析失败: {str(e)}") from e
    except Exception as e:
        raise ShowDocParseError(f"解码 page_content 失败: {str(e)}") from e


def find_category_by_name(
    categories: List[Dict[str, Any]], 
    name: str,
    recursive: bool = True
) -> Optional[Dict[str, Any]]:
    """
    在目录树中递归查找指定名称的分类
    
    Args:
        categories: 分类列表（从 API 返回的目录树数据）
        name: 要查找的分类名称
        recursive: 是否递归查找子分类
    
    Returns:
        找到的分类字典，未找到返回 None
    """
    if not name or name.lower() in ("全部", "all", "all"):
        return None  # 表示获取全部
    
    name = name.strip()
    
    def search_recursive(cat_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for cat in cat_list:
            # 检查当前分类名称
            cat_name = cat.get("cat_name", "")
            if cat_name == name:
                return cat
            
            # 递归查找子分类
            if recursive:
                children = cat.get("catalogs", [])
                if children:
                    result = search_recursive(children)
                    if result:
                        return result
        
        return None
    
    return search_recursive(categories)


def filter_categories_by_name(
    categories: List[Dict[str, Any]],
    name: Optional[str]
) -> List[Dict[str, Any]]:
    """
    根据节点名称筛选分类列表
    
    Args:
        categories: 完整的分类列表
        name: 节点名称，None、"全部"、"all" 表示返回所有
    
    Returns:
        筛选后的分类列表
    """
    if not name or name.strip().lower() in ("全部", "all"):
        return categories
    
    target_cat = find_category_by_name(categories, name)
    if target_cat:
        # 返回找到的分类（包含其所有子分类）
        return [target_cat]
    else:
        # 未找到，返回空列表
        return []


def build_category_tree(
    category_data: Dict[str, Any],
    item_id: str
) -> List[Dict[str, Any]]:
    """
    将 API 返回的扁平化分类数据转换为树状结构
    
    Args:
        category_data: API 返回的目录数据
        item_id: 项目 ID
    
    Returns:
        树状结构的分类列表
    """
    # API 返回的数据已经是树状结构（通过 parent_cat_id 和 catalogs 字段）
    # 这里主要是提取顶层分类
    if isinstance(category_data, dict):
        if "menu" in category_data:
            menu = category_data["menu"]
            if "catalogs" in menu:
                return menu["catalogs"]
        elif "catalogs" in category_data:
            return category_data["catalogs"]
    
    return []

