"""
文件格式处理工具

支持 JSON、YAML、XML、TOML、Markdown 等格式的读写和处理。
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import re

from .exceptions import FileOperationError
from .content_processor import read_file_safe
from .safe_writer import SafeFileWriter

# 可选依赖
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import xml.etree.ElementTree as ET
    XML_AVAILABLE = True
except ImportError:
    XML_AVAILABLE = False

try:
    import tomllib
    TOML_AVAILABLE = True
except ImportError:
    try:
        import tomli as tomllib
        TOML_AVAILABLE = True
    except ImportError:
        TOML_AVAILABLE = False


# JSON 处理
def read_json(
    file_path: str | Path,
    encoding: str = "utf-8",
) -> Any:
    """
    读取 JSON 文件
    
    Args:
        file_path: 文件路径
        encoding: 文件编码
    
    Returns:
        JSON 数据
    
    Raises:
        FileNotFoundError: 文件不存在
        FileOperationError: JSON 解析错误
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    content = read_file_safe(path, encoding=encoding)
    
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise FileOperationError(f"JSON 解析错误: {e}")


def write_json(
    file_path: str | Path,
    data: Any,
    indent: int = 2,
    ensure_ascii: bool = False,
    encoding: str = "utf-8",
) -> Path:
    """
    写入 JSON 文件
    
    Args:
        file_path: 文件路径
        data: 要写入的数据
        indent: 缩进空格数
        ensure_ascii: 是否确保 ASCII 编码
        encoding: 文件编码
    
    Returns:
        文件路径
    
    Raises:
        FileOperationError: JSON 序列化错误
    """
    path = Path(file_path)
    
    try:
        content = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
    except (TypeError, ValueError) as e:
        raise FileOperationError(f"JSON 序列化错误: {e}")
    
    writer = SafeFileWriter(path, encoding=encoding, backup=False)
    writer.write(content)
    
    return path


# YAML 处理
def read_yaml(
    file_path: str | Path,
    encoding: str = "utf-8",
) -> Any:
    """
    读取 YAML 文件
    
    Args:
        file_path: 文件路径
        encoding: 文件编码
    
    Returns:
        YAML 数据
    
    Raises:
        FileNotFoundError: 文件不存在
        FileOperationError: YAML 解析错误或未安装 PyYAML
    """
    if not YAML_AVAILABLE:
        raise FileOperationError("未安装 PyYAML，请运行: pip install pyyaml")
    
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    content = read_file_safe(path, encoding=encoding)
    
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise FileOperationError(f"YAML 解析错误: {e}")


def write_yaml(
    file_path: str | Path,
    data: Any,
    default_flow_style: bool = False,
    encoding: str = "utf-8",
) -> Path:
    """
    写入 YAML 文件
    
    Args:
        file_path: 文件路径
        data: 要写入的数据
        default_flow_style: 是否使用流式风格
        encoding: 文件编码
    
    Returns:
        文件路径
    
    Raises:
        FileOperationError: YAML 序列化错误或未安装 PyYAML
    """
    if not YAML_AVAILABLE:
        raise FileOperationError("未安装 PyYAML，请运行: pip install pyyaml")
    
    path = Path(file_path)
    
    try:
        content = yaml.dump(data, default_flow_style=default_flow_style, allow_unicode=True)
    except Exception as e:
        raise FileOperationError(f"YAML 序列化错误: {e}")
    
    writer = SafeFileWriter(path, encoding=encoding, backup=False)
    writer.write(content)
    
    return path


# XML 处理
def read_xml(
    file_path: str | Path,
    encoding: str = "utf-8",
) -> ET.Element:
    """
    读取 XML 文件
    
    Args:
        file_path: 文件路径
        encoding: 文件编码
    
    Returns:
        XML 根元素
    
    Raises:
        FileNotFoundError: 文件不存在
        FileOperationError: XML 解析错误
    """
    if not XML_AVAILABLE:
        raise FileOperationError("XML 支持不可用")
    
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError as e:
        raise FileOperationError(f"XML 解析错误: {e}")


def write_xml(
    file_path: str | Path,
    root: ET.Element,
    encoding: str = "utf-8",
    xml_declaration: bool = True,
) -> Path:
    """
    写入 XML 文件
    
    Args:
        file_path: 文件路径
        root: XML 根元素
        encoding: 文件编码
        xml_declaration: 是否包含 XML 声明
    
    Returns:
        文件路径
    
    Raises:
        FileOperationError: XML 序列化错误
    """
    if not XML_AVAILABLE:
        raise FileOperationError("XML 支持不可用")
    
    path = Path(file_path)
    
    try:
        tree = ET.ElementTree(root)
        tree.write(
            path,
            encoding=encoding,
            xml_declaration=xml_declaration,
        )
    except Exception as e:
        raise FileOperationError(f"XML 写入错误: {e}")
    
    return path


# TOML 处理
def read_toml(
    file_path: str | Path,
    encoding: str = "utf-8",
) -> Dict[str, Any]:
    """
    读取 TOML 文件
    
    Args:
        file_path: 文件路径
        encoding: 文件编码
    
    Returns:
        TOML 数据字典
    
    Raises:
        FileNotFoundError: 文件不存在
        FileOperationError: TOML 解析错误或未安装 tomli
    """
    if not TOML_AVAILABLE:
        raise FileOperationError("未安装 tomli，请运行: pip install tomli")
    
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    content = read_file_safe(path, encoding=encoding)
    
    try:
        return tomllib.loads(content)
    except Exception as e:
        raise FileOperationError(f"TOML 解析错误: {e}")


def write_toml(
    file_path: str | Path,
    data: Dict[str, Any],
    encoding: str = "utf-8",
) -> Path:
    """
    写入 TOML 文件
    
    Args:
        file_path: 文件路径
        data: 要写入的数据
        encoding: 文件编码
    
    Returns:
        文件路径
    
    Raises:
        FileOperationError: TOML 序列化错误或未安装 tomli-w
    """
    try:
        import tomli_w
    except ImportError:
        raise FileOperationError("未安装 tomli-w，请运行: pip install tomli-w")
    
    path = Path(file_path)
    
    try:
        content = tomli_w.dumps(data)
    except Exception as e:
        raise FileOperationError(f"TOML 序列化错误: {e}")
    
    writer = SafeFileWriter(path, encoding=encoding, backup=False)
    writer.write(content)
    
    return path


# Markdown 处理
def extract_markdown_headings(markdown_content: str) -> List[Dict[str, Any]]:
    """
    提取 Markdown 标题
    
    Args:
        markdown_content: Markdown 内容
    
    Returns:
        标题列表，每个标题包含：
        - level: 级别（1-6）
        - text: 标题文本
        - line_number: 行号
    """
    headings = []
    lines = markdown_content.splitlines()
    
    for i, line in enumerate(lines, 1):
        # 匹配 ATX 风格标题（# ## ###）
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append({
                "level": level,
                "text": text,
                "line_number": i,
            })
    
    return headings


def generate_markdown_toc(markdown_content: str, max_depth: int = 3) -> str:
    """
    生成 Markdown 目录（TOC）
    
    Args:
        markdown_content: Markdown 内容
        max_depth: 最大深度
    
    Returns:
        目录字符串
    """
    headings = extract_markdown_headings(markdown_content)
    
    toc_lines = ["## 目录\n"]
    
    for heading in headings:
        if heading["level"] > max_depth:
            continue
        
        indent = "  " * (heading["level"] - 1)
        anchor = re.sub(r'[^\w\s-]', '', heading["text"]).strip()
        anchor = re.sub(r'[-\s]+', '-', anchor).lower()
        
        toc_lines.append(f"{indent}- [{heading['text']}](#{anchor})")
    
    return "\n".join(toc_lines)

