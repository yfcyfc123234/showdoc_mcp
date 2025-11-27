"""
ShowDoc 数据模型定义
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ApiDefinition:
    """API 接口定义"""
    method: str  # GET, POST 等
    url: str
    title: str
    description: str = ""
    request: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    headers: Optional[List[Dict[str, Any]]] = None
    query: Optional[List[Dict[str, Any]]] = None
    body: Optional[Dict[str, Any]] = None


@dataclass
class Page:
    """页面信息"""
    page_id: str
    page_title: str
    cat_id: str
    author_uid: str = ""
    author_username: str = ""
    api_info: Optional[ApiDefinition] = None
    ext_info: Optional[Dict[str, Any]] = None
    # 原始 page_content 解析后的完整数据
    raw_content: Optional[Dict[str, Any]] = None


@dataclass
class Category:
    """分类节点（支持嵌套）"""
    cat_id: str
    cat_name: str
    item_id: str
    parent_cat_id: str
    level: int
    s_number: str = ""
    pages: List[Page] = field(default_factory=list)
    children: List['Category'] = field(default_factory=list)  # 子分类


@dataclass
class ItemInfo:
    """文档项目信息"""
    item_id: str
    item_name: str
    item_domain: str = ""
    is_archived: str = "0"
    default_page_id: Optional[str] = None
    default_cat_id2: Optional[str] = None
    default_cat_id3: Optional[str] = None
    default_cat_id4: Optional[str] = None


@dataclass
class ApiTree:
    """完整的接口树结构"""
    item_info: ItemInfo
    categories: List[Category] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        def category_to_dict(cat: Category) -> Dict[str, Any]:
            return {
                "cat_id": cat.cat_id,
                "cat_name": cat.cat_name,
                "level": cat.level,
                "parent_cat_id": cat.parent_cat_id,
                "pages": [
                    {
                        "page_id": page.page_id,
                        "page_title": page.page_title,
                        "api_info": {
                            "method": page.api_info.method,
                            "url": page.api_info.url,
                            "title": page.api_info.title,
                            "description": page.api_info.description,
                            "request": page.api_info.request,
                            "response": page.api_info.response,
                        } if page.api_info else None
                    }
                    for page in cat.pages
                ],
                "children": [category_to_dict(child) for child in cat.children]
            }
        
        return {
            "item_info": {
                "item_id": self.item_info.item_id,
                "item_name": self.item_info.item_name,
            },
            "categories": [category_to_dict(cat) for cat in self.categories]
        }

