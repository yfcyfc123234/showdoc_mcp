"""
Cursor Cloud Agents API 客户端
支持动态 API Key 和缓存机制
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests
from requests.auth import HTTPBasicAuth


class CursorAgentsClient:
    """Cursor Cloud Agents API 客户端"""
    
    BASE_URL = "https://api.cursor.com/v0"
    CACHE_DIR = Path.home() / ".cursor" / "mcp_cache"
    API_KEY_FILE = CACHE_DIR / "api_key.json"
    # 用户信息缓存文件（在项目 output 目录下）
    OUTPUT_DIR = Path.cwd() / "output"
    USER_INFO_FILE = OUTPUT_DIR / ".cursor_api_key_info.json"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            api_key: API 密钥，如果为 None 则从缓存读取
        """
        self.api_key = api_key or self._load_api_key()
        if not self.api_key:
            raise ValueError("API Key 未设置，请先设置 API Key")
        
        # 确保缓存目录存在
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_api_key(self) -> Optional[str]:
        """从缓存文件加载 API Key"""
        if self.API_KEY_FILE.exists():
            try:
                with open(self.API_KEY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('api_key')
            except Exception:
                return None
        return None
    
    def _save_api_key(self, api_key: str) -> None:
        """保存 API Key 到缓存文件"""
        try:
            with open(self.API_KEY_FILE, 'w', encoding='utf-8') as f:
                json.dump({'api_key': api_key}, f, indent=2)
        except Exception as e:
            raise RuntimeError(f"保存 API Key 失败: {e}")
    
    def _load_user_info(self) -> Optional[Dict[str, Any]]:
        """从缓存文件加载用户信息"""
        if self.USER_INFO_FILE.exists():
            try:
                with open(self.USER_INFO_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return None
        return None
    
    def _save_user_info(self, user_info: Dict[str, Any]) -> None:
        """保存用户信息到缓存文件"""
        try:
            with open(self.USER_INFO_FILE, 'w', encoding='utf-8') as f:
                json.dump(user_info, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise RuntimeError(f"保存用户信息失败: {e}")
    
    def get_cached_user_info(self) -> Optional[Dict[str, Any]]:
        """
        获取缓存的用户信息
        
        Returns:
            用户信息字典，如果不存在则返回 None
        """
        return self._load_user_info()
    
    def set_api_key(self, api_key: str, fetch_user_info: bool = True) -> Dict[str, Any]:
        """
        设置并缓存 API Key，首次设置时会自动获取并缓存用户信息
        
        Args:
            api_key: API 密钥
            fetch_user_info: 是否获取用户信息（默认 True，首次设置时建议为 True）
        
        Returns:
            包含设置结果的字典，如果获取了用户信息则包含 user_info 字段
        """
        self.api_key = api_key
        self._save_api_key(api_key)
        
        result = {
            "ok": True,
            "message": "API Key 已设置并缓存"
        }
        
        # 如果启用获取用户信息，且缓存中不存在，则调用 API 获取
        if fetch_user_info:
            cached_info = self._load_user_info()
            if not cached_info:
                try:
                    user_info = self.get_api_key_info()
                    self._save_user_info(user_info)
                    result["user_info"] = user_info
                    result["message"] = "API Key 已设置并缓存，用户信息已获取并缓存"
                except Exception as e:
                    # 获取用户信息失败不影响 API Key 的设置
                    result["warning"] = f"获取用户信息失败: {e}"
            else:
                result["user_info"] = cached_info
                result["message"] = "API Key 已设置并缓存，使用缓存的用户信息"
        
        return result
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法 (GET, POST, DELETE)
            endpoint: API 端点路径
            params: URL 查询参数
            json_data: JSON 请求体
        
        Returns:
            API 响应数据
        """
        url = f"{self.BASE_URL}{endpoint}"
        auth = HTTPBasicAuth(self.api_key, '')
        
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                auth=auth,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ValueError("API Key 无效或已过期")
            raise RuntimeError(f"API 请求失败: {e}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"网络请求失败: {e}")
    
    def list_agents(self, limit: int = 20, cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        列出所有云端代理
        
        Args:
            limit: 返回的云端代理数量（默认 20，最大 100）
            cursor: 分页游标
        
        Returns:
            包含 agents 列表和 nextCursor 的字典
        """
        params = {'limit': min(limit, 100)}
        if cursor:
            params['cursor'] = cursor
        return self._request('GET', '/agents', params=params)
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """
        获取云端 Agent 的当前状态和结果
        
        Args:
            agent_id: 云端 Agent 的唯一标识符
        
        Returns:
            Agent 状态信息
        """
        return self._request('GET', f'/agents/{agent_id}')
    
    def get_agent_conversation(self, agent_id: str) -> Dict[str, Any]:
        """
        获取云端 Agent 的会话历史
        
        Args:
            agent_id: 云端 Agent 的唯一标识符
        
        Returns:
            包含会话消息的字典
        """
        return self._request('GET', f'/agents/{agent_id}/conversation')
    
    def add_followup(
        self,
        agent_id: str,
        text: str,
        images: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        为现有云代理添加后续指令
        
        Args:
            agent_id: 云代理的唯一标识符
            text: 后续指令文本
            images: 图片对象数组（最多 5 个），每个包含 data (base64) 和 dimension (width, height)
        
        Returns:
            包含 agent id 的响应
        """
        if images and len(images) > 5:
            raise ValueError("最多只能提供 5 张图片")
        
        prompt = {'text': text}
        if images:
            prompt['images'] = images
        
        return self._request('POST', f'/agents/{agent_id}/followup', json_data={'prompt': prompt})
    
    def delete_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        删除云代理
        
        Args:
            agent_id: 云代理的唯一标识符
        
        Returns:
            包含 agent id 的响应
        """
        return self._request('DELETE', f'/agents/{agent_id}')
    
    def get_api_key_info(self) -> Dict[str, Any]:
        """
        获取用于身份验证的 API 密钥相关信息
        
        Returns:
            API 密钥信息
        """
        return self._request('GET', '/me')
    
    def list_models(self) -> Dict[str, Any]:
        """
        获取云端代理的推荐模型列表
        
        Returns:
            包含模型列表的字典
        """
        return self._request('GET', '/models')
    
    def list_repositories(self) -> Dict[str, Any]:
        """
        获取已认证用户可访问的 GitHub 仓库列表
        
        注意：此端点有严格的速率限制（1 次/用户/分钟，30 次/用户/小时）
        
        Returns:
            包含仓库列表的字典
        """
        return self._request('GET', '/repositories')

