"""
Cookie 管理器 - 用于保存和加载登录 Cookie
类似浏览器的会话管理，将 Cookie 与 URL 对应保存
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse


class CookieManager:
    """Cookie 管理器，负责保存和加载 Cookie"""
    
    # Cookie 默认过期时间（24小时）
    DEFAULT_EXPIRY_HOURS = 24
    
    def __init__(self, cookie_file: Optional[Path] = None):
        """
        初始化 Cookie 管理器
        
        Args:
            cookie_file: Cookie 文件路径，如果为 None 则使用默认路径
        """
        if cookie_file is None:
            # 默认保存在 output/.showdoc_cookies.json（统一输出目录）
            cookie_file = Path.cwd() / "output" / ".showdoc_cookies.json"
        self.cookie_file = Path(cookie_file)
        self.cookies_data: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._load_cookies()
    
    def _load_cookies(self) -> None:
        """从文件加载 Cookie 数据"""
        if self.cookie_file.exists():
            try:
                with open(self.cookie_file, "r", encoding="utf-8") as f:
                    self.cookies_data = json.load(f)
            except Exception:
                self.cookies_data = {}
        else:
            self.cookies_data = {}
    
    def _save_cookies(self) -> None:
        """保存 Cookie 数据到文件"""
        try:
            self.cookie_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cookie_file, "w", encoding="utf-8") as f:
                json.dump(self.cookies_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _normalize_server_base(self, server_base: str) -> str:
        """规范化服务器地址"""
        # 移除末尾的斜杠
        server_base = server_base.rstrip('/')
        # 确保以 http:// 或 https:// 开头
        if not server_base.startswith(('http://', 'https://')):
            server_base = 'https://' + server_base
        return server_base
    
    def get_cookie(self, server_base: str, item_id: str) -> Optional[str]:
        """
        获取指定 URL 的 Cookie
        
        Args:
            server_base: 服务器地址
            item_id: 项目 ID
            
        Returns:
            Cookie 字符串，如果不存在或已过期则返回 None
        """
        server_base = self._normalize_server_base(server_base)
        
        if server_base not in self.cookies_data:
            return None
        
        if item_id not in self.cookies_data[server_base]:
            return None
        
        cookie_info = self.cookies_data[server_base][item_id]
        cookie = cookie_info.get("cookie")
        timestamp_str = cookie_info.get("timestamp")
        
        if not cookie or not timestamp_str:
            return None
        
        # 检查是否过期
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            expiry_hours = cookie_info.get("expiry_hours", self.DEFAULT_EXPIRY_HOURS)
            if datetime.now() - timestamp > timedelta(hours=expiry_hours):
                # Cookie 已过期，删除它
                del self.cookies_data[server_base][item_id]
                if not self.cookies_data[server_base]:
                    del self.cookies_data[server_base]
                self._save_cookies()
                return None
        except Exception:
            # 解析时间戳失败，认为已过期
            return None
        
        return cookie
    
    def save_cookie(self, server_base: str, item_id: str, cookie: str, expiry_hours: int = DEFAULT_EXPIRY_HOURS) -> None:
        """
        保存 Cookie
        
        Args:
            server_base: 服务器地址
            item_id: 项目 ID
            cookie: Cookie 字符串
            expiry_hours: Cookie 过期时间（小时），默认 24 小时
        """
        server_base = self._normalize_server_base(server_base)
        
        if server_base not in self.cookies_data:
            self.cookies_data[server_base] = {}
        
        self.cookies_data[server_base][item_id] = {
            "cookie": cookie,
            "timestamp": datetime.now().isoformat(),
            "expiry_hours": expiry_hours,
        }
        
        self._save_cookies()
    
    def delete_cookie(self, server_base: str, item_id: str) -> None:
        """
        删除指定 URL 的 Cookie
        
        Args:
            server_base: 服务器地址
            item_id: 项目 ID
        """
        server_base = self._normalize_server_base(server_base)
        
        if server_base in self.cookies_data:
            if item_id in self.cookies_data[server_base]:
                del self.cookies_data[server_base][item_id]
                if not self.cookies_data[server_base]:
                    del self.cookies_data[server_base]
                self._save_cookies()
    
    def clear_all_cookies(self) -> None:
        """清空所有 Cookie"""
        self.cookies_data = {}
        self._save_cookies()
        if self.cookie_file.exists():
            self.cookie_file.unlink()

