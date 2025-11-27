"""
代码生成工具函数
"""
import re
import os
from typing import Optional

# 翻译器缓存（避免重复初始化）
_translator_cache = {}

# 翻译结果缓存（避免重复翻译相同文本）
_translation_cache = {}


def _get_google_translator():
    """获取 Google 翻译器（免费，无需 API 密钥）"""
    try:
        from googletrans import Translator
        if 'google' not in _translator_cache:
            _translator_cache['google'] = Translator()
        return _translator_cache['google']
    except (ImportError, Exception):
        # 导入失败或初始化失败，返回 None
        return None


def _translate_with_google(text: str) -> Optional[str]:
    """使用 Google 翻译（免费）"""
    try:
        translator = _get_google_translator()
        if not translator:
            return None
        
        result = translator.translate(text, src='zh', dest='en')
        if result and result.text:
            # 清理翻译结果，移除特殊字符
            translated = result.text.strip()
            # 如果翻译结果是原文本（可能翻译失败），返回 None
            if translated == text:
                return None
            return translated
    except Exception:
        # 翻译失败，静默处理
        pass
    return None


def _translate_with_microsoft(text: str, api_key: Optional[str] = None, endpoint: Optional[str] = None) -> Optional[str]:
    """使用微软翻译 API（需要 API 密钥，每月免费 200 万字符）"""
    if not api_key:
        # 尝试从环境变量读取
        api_key = os.getenv('MICROSOFT_TRANSLATOR_KEY')
        endpoint = os.getenv('MICROSOFT_TRANSLATOR_ENDPOINT', 'https://api.cognitive.microsofttranslator.com')
    
    if not api_key:
        return None
    
    try:
        import requests
        import uuid
        
        # 构建请求
        path = '/translate'
        constructed_url = endpoint + path
        
        params = {
            'api-version': '3.0',
            'from': 'zh',
            'to': 'en'
        }
        
        headers = {
            'Ocp-Apim-Subscription-Key': api_key,
            'Ocp-Apim-Subscription-Region': os.getenv('MICROSOFT_TRANSLATOR_REGION', 'global'),
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }
        
        body = [{'text': text}]
        
        response = requests.post(constructed_url, params=params, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result and len(result) > 0 and 'translations' in result[0]:
            translated = result[0]['translations'][0]['text']
            if translated and translated != text:
                return translated.strip()
    except Exception:
        # 翻译失败，静默处理
        pass
    return None


def translate_chinese_to_english(text: str, use_translation_api: bool = True) -> str:
    """
    将中文转换为英文
    
    支持的翻译方式（按优先级）：
    1. 翻译结果缓存（避免重复翻译）
    2. Google 翻译（免费，无需 API 密钥）
    3. 微软翻译 API（需要配置 API 密钥，每月免费 200 万字符）
    4. 最小映射表（仅作为最后兜底）
    
    配置微软翻译 API：
    - 设置环境变量 MICROSOFT_TRANSLATOR_KEY（必需）
    - 可选：MICROSOFT_TRANSLATOR_ENDPOINT（默认使用官方端点）
    - 可选：MICROSOFT_TRANSLATOR_REGION（默认 'global'）
    
    获取 API 密钥：
    1. 访问 https://portal.azure.com/
    2. 创建"翻译器"服务
    3. 获取密钥和区域
    
    Args:
        text: 要翻译的中文文本
        use_translation_api: 是否使用翻译 API（默认 True）
    
    Returns:
        翻译后的英文文本，如果翻译失败则使用映射表或返回清理后的文本
    """
    if not text:
        return ""
    
    # 检查缓存（避免重复翻译相同文本）
    if text in _translation_cache:
        return _translation_cache[text]
    
    # 检查是否包含中文字符
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
    if not has_chinese:
        # 如果没有中文，直接清理并返回
        result = re.sub(r'[^\w\-]', '', text)
        result = result if result else "item"
        _translation_cache[text] = result
        return result
    
    # 如果启用翻译 API，尝试使用翻译
    if use_translation_api:
        # 1. 优先尝试使用微软翻译 API（更稳定、准确）
        translated = _translate_with_microsoft(text)
        if translated:
            # 清理翻译结果
            result = re.sub(r'[^\w\s\-]', '', translated)
            result = re.sub(r'\s+', '_', result).strip('_')
            if result and result.isascii():
                result = result.lower()
                _translation_cache[text] = result
                return result
        
        # 2. 如果微软翻译失败，尝试使用 Google 翻译（免费）
        translated = _translate_with_google(text)
        if translated:
            # 清理翻译结果
            result = re.sub(r'[^\w\s\-]', '', translated)
            result = re.sub(r'\s+', '_', result).strip('_')
            if result and result.isascii():
                result = result.lower()
                _translation_cache[text] = result
                return result
    
    # 3. 最后兜底：最小映射表（只保留最常用的）
    minimal_mapping = {
        "新接口": "newapi",
        "应用": "app",
        "接口": "api",
        "根目录": "root",
        "默认": "default",
    }
    
    # 先尝试完整匹配
    if text in minimal_mapping:
        result = minimal_mapping[text].lower()
        _translation_cache[text] = result
        return result
    
    # 尝试部分匹配替换
    result = text
    for chinese, english in minimal_mapping.items():
        if chinese in result:
            result = result.replace(chinese, english)
    
    # 如果还有中文字符，移除中文字符
    result = re.sub(r'[^\w\-]', '', result)
    
    # 如果处理后为空或仍包含非ASCII字符，使用默认名称
    if not result or not result.isascii():
        result = "item"
    else:
        result = result.lower()
    
    _translation_cache[text] = result
    return result


def to_pascal_case(text: str) -> str:
    """转换为帕斯卡命名（首字母大写驼峰）"""
    # 先转换为英文
    text = translate_chinese_to_english(text)
    
    # 按非字母数字字符分割
    words = re.sub(r'[^\w]', '_', text).split('_')
    words = [w for w in words if w]
    
    if not words:
        return "Item"
    
    # 首字母大写，其余小写
    return ''.join(word.capitalize() for word in words)


def to_camel_case(text: str) -> str:
    """转换为驼峰命名（首字母小写驼峰）"""
    pascal = to_pascal_case(text)
    if not pascal:
        return "item"
    return pascal[0].lower() + pascal[1:] if len(pascal) > 1 else pascal.lower()


def sanitize_class_name(name: str) -> str:
    """清理类名，确保符合 Kotlin 规范"""
    # 转换为帕斯卡命名
    name = to_pascal_case(name)
    
    # Kotlin 关键字列表
    kotlin_keywords = {
        "val", "var", "fun", "class", "object", "interface",
        "if", "else", "when", "for", "while", "do", "try", "catch",
        "return", "break", "continue", "null", "true", "false",
        "this", "super", "is", "as", "in", "out", "typealias",
        "package", "import", "as", "typealias", "typeof"
    }
    
    if name.lower() in kotlin_keywords:
        name = name + "Type"
    
    # 确保以字母开头
    if name and not name[0].isalpha():
        name = "A" + name
    
    return name


def sanitize_method_name(name: str) -> str:
    """清理方法名，确保符合 Kotlin 规范"""
    name = to_camel_case(name)
    
    # Kotlin 关键字
    kotlin_keywords = {
        "val", "var", "fun", "class", "object", "interface",
        "if", "else", "when", "for", "while", "do", "try", "catch",
        "return", "break", "continue", "null", "true", "false",
        "this", "super", "is", "as", "in", "out", "typealias"
    }
    
    if name.lower() in kotlin_keywords:
        name = name + "Method"
    
    # 确保以字母开头
    if name and not name[0].isalpha():
        name = "a" + name
    
    return name


def extract_name_from_url(url: str) -> Optional[str]:
    """
    从 URL 路径中提取方法名或类名
    
    例如:
    - /api/v1/sendsms -> sendsms
    - /api/v1/logout -> logout
    - /api/v1/start_use -> startUse
    - /api/v1/orderVerify -> orderVerify
    """
    if not url:
        return None
    
    # 移除协议和域名
    if "://" in url:
        parts = url.split("/")
        url = "/" + "/".join(parts[3:]) if len(parts) > 3 else "/"
    
    # 移除查询参数
    if "?" in url:
        url = url.split("?")[0]
    
    # 移除模板变量
    url = url.replace("{{baseurl}}", "").replace("{{baseUrl}}", "").strip()
    
    # 提取路径的最后一部分
    parts = [p for p in url.rstrip("/").split("/") if p]
    if not parts:
        return None
    
    last_part = parts[-1]
    
    # 移除路径参数 {param}
    last_part = re.sub(r'\{[^}]+\}', '', last_part)
    
    if not last_part:
        # 如果最后一部分被移除了，使用倒数第二部分
        if len(parts) > 1:
            last_part = parts[-2]
        else:
            return None
    
    return last_part


def url_path_to_method_name(url: str) -> str:
    """
    将 URL 路径转换为方法名（驼峰命名）
    
    例如:
    - /api/v1/sendsms -> sendSms
    - /api/v1/logout -> logout
    - /api/v1/start_use -> startUse
    - /api/v1/orderVerify -> orderVerify
    - /api/v1/user_app -> userApp
    """
    path_name = extract_name_from_url(url)
    if not path_name:
        return "apiCall"
    
    # 将下划线、连字符转换为驼峰命名
    # 支持多种分隔符: _ - 
    parts = re.split(r'[_\-]', path_name)
    
    if len(parts) == 1:
        # 单个单词，检查是否已经是驼峰命名（如 orderVerify）
        # 如果有小写+大写的情况，保持原样，否则转为小写
        if path_name[0].isupper() and len(path_name) > 1:
            # 如果首字母大写，转为小写驼峰
            return path_name[0].lower() + path_name[1:]
        # 如果全小写，直接返回
        return path_name.lower()
    else:
        # 多个单词，转换为驼峰命名
        # 第一个单词全小写，后续单词首字母大写
        result = parts[0].lower()
        for part in parts[1:]:
            if part:
                result += part.capitalize()
        return result


def url_path_to_class_name(url: str, suffix: str = "", depth: int = 1) -> str:
    """
    将 URL 路径转换为类名（帕斯卡命名）
    
    例如:
    - /api/v1/sendsms, depth=1 -> SendSms
    - /api/v1/config, depth=1 -> Config
    - /api/v1/ad/config, depth=1 -> Config
    - /api/v1/ad/config, depth=2 -> AdConfig
    
    Args:
        url: URL 路径
        suffix: 后缀（如 "Bean"）
        depth: 使用路径的深度（从后往前数，1表示只用最后一段，2表示用最后两段）
    """
    # 移除协议和域名
    clean_url = url
    if "://" in clean_url:
        parts = clean_url.split("/")
        clean_url = "/" + "/".join(parts[3:]) if len(parts) > 3 else "/"
    
    # 移除查询参数
    if "?" in clean_url:
        clean_url = clean_url.split("?")[0]
    
    # 移除模板变量
    clean_url = clean_url.replace("{{baseurl}}", "").replace("{{baseUrl}}", "").strip()
    
    # 提取路径段
    parts = [p for p in clean_url.rstrip("/").split("/") if p]
    if not parts:
        return "Api" + suffix
    
    # 根据 depth 提取最后 N 个路径段
    if depth > len(parts):
        depth = len(parts)
    
    selected_parts = parts[-depth:]
    
    # 移除路径参数 {param}
    selected_parts = [re.sub(r'\{[^}]+\}', '', p) for p in selected_parts]
    selected_parts = [p for p in selected_parts if p]  # 移除空字符串
    
    if not selected_parts:
        return "Api" + suffix
    
    # 将路径段组合并转换为帕斯卡命名
    # 例如: ['ad', 'config'] -> 'AdConfig'
    class_name_parts = []
    for part in selected_parts:
        # 处理下划线和连字符
        sub_parts = re.split(r'[_\-]', part)
        for sub_part in sub_parts:
            if sub_part:
                class_name_parts.append(sub_part.capitalize())
    
    class_name = ''.join(class_name_parts) if class_name_parts else "Api"
    
    if suffix and not class_name.endswith(suffix):
        class_name += suffix
    
    return class_name

