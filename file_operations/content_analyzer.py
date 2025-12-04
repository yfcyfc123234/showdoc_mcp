"""
文件内容分析工具

提供代码行数统计、文件大小分析、全文搜索等功能。
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Pattern
from collections import Counter

# 使用内置异常
from .content_processor import read_file_safe


def count_lines(
    file_path: str | Path,
    encoding: Optional[str] = None,
) -> Dict[str, int]:
    """
    统计代码行数
    
    Args:
        file_path: 文件路径
        encoding: 文件编码
    
    Returns:
        统计结果字典，包含：
        - total_lines: 总行数
        - code_lines: 代码行数（排除空行和注释）
        - blank_lines: 空行数
        - comment_lines: 注释行数
        - max_line_length: 最长行长度
    
    Raises:
        FileNotFoundError: 文件不存在
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    content = read_file_safe(path, encoding=encoding)
    lines = content.splitlines()
    
    total_lines = len(lines)
    blank_lines = 0
    comment_lines = 0
    code_lines = 0
    max_line_length = 0
    
    # 简单的注释检测（支持 Python、JavaScript、Kotlin、Dart 等）
    comment_patterns = [
        re.compile(r'^\s*#'),  # Python 单行注释
        re.compile(r'^\s*//'),  # JavaScript/Kotlin/Dart 单行注释
        re.compile(r'^\s*\*'),  # 多行注释中的行
    ]
    
    for line in lines:
        line_length = len(line)
        if line_length > max_line_length:
            max_line_length = line_length
        
        stripped = line.strip()
        
        if not stripped:
            blank_lines += 1
        else:
            # 检查是否是注释
            is_comment = False
            for pattern in comment_patterns:
                if pattern.match(line):
                    is_comment = True
                    break
            
            if is_comment:
                comment_lines += 1
            else:
                code_lines += 1
    
    return {
        "total_lines": total_lines,
        "code_lines": code_lines,
        "blank_lines": blank_lines,
        "comment_lines": comment_lines,
        "max_line_length": max_line_length,
    }


def analyze_file_size(
    file_path: str | Path,
) -> Dict[str, Any]:
    """
    分析文件大小
    
    Args:
        file_path: 文件路径
    
    Returns:
        分析结果字典，包含：
        - size_bytes: 文件大小（字节）
        - size_kb: 文件大小（KB）
        - size_mb: 文件大小（MB）
        - size_gb: 文件大小（GB）
        - human_readable: 人类可读的大小字符串
    
    Raises:
        FileNotFoundError: 文件不存在
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    size_bytes = path.stat().st_size
    
    size_kb = size_bytes / 1024
    size_mb = size_kb / 1024
    size_gb = size_mb / 1024
    
    # 生成人类可读的大小
    if size_gb >= 1:
        human_readable = f"{size_gb:.2f} GB"
    elif size_mb >= 1:
        human_readable = f"{size_mb:.2f} MB"
    elif size_kb >= 1:
        human_readable = f"{size_kb:.2f} KB"
    else:
        human_readable = f"{size_bytes} B"
    
    return {
        "size_bytes": size_bytes,
        "size_kb": round(size_kb, 2),
        "size_mb": round(size_mb, 2),
        "size_gb": round(size_gb, 2),
        "human_readable": human_readable,
    }


def search_text(
    file_path: str | Path,
    search_pattern: str | Pattern,
    regex: bool = False,
    case_sensitive: bool = False,
    encoding: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    在文件中搜索文本
    
    Args:
        file_path: 文件路径
        search_pattern: 搜索模式（字符串或正则表达式）
        regex: 是否使用正则表达式
        case_sensitive: 是否区分大小写
        encoding: 文件编码
    
    Returns:
        匹配结果列表，每个结果包含：
        - line_number: 行号
        - column: 列号
        - match_text: 匹配的文本
        - line_content: 行内容
        - context_before: 前几行内容（可选）
        - context_after: 后几行内容（可选）
    
    Raises:
        FileNotFoundError: 文件不存在
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    content = read_file_safe(path, encoding=encoding)
    lines = content.splitlines()
    
    matches = []
    
    # 准备搜索模式
    if regex:
        if isinstance(search_pattern, str):
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(search_pattern, flags)
        else:
            pattern = search_pattern
    else:
        if case_sensitive:
            pattern = re.compile(re.escape(search_pattern))
        else:
            pattern = re.compile(re.escape(search_pattern), re.IGNORECASE)
    
    # 搜索
    for line_num, line in enumerate(lines, 1):
        for match in pattern.finditer(line):
            matches.append({
                "line_number": line_num,
                "column": match.start() + 1,
                "match_text": match.group(),
                "line_content": line,
                "start": match.start(),
                "end": match.end(),
            })
    
    return matches


def count_words(
    file_path: str | Path,
    encoding: Optional[str] = None,
) -> Dict[str, Any]:
    """
    统计文件中的单词数
    
    Args:
        file_path: 文件路径
        encoding: 文件编码
    
    Returns:
        统计结果字典，包含：
        - total_words: 总单词数
        - unique_words: 唯一单词数
        - total_chars: 总字符数
        - total_chars_no_spaces: 不含空格的字符数
        - word_frequency: 单词频率字典（前10个最常见的单词）
    
    Raises:
        FileNotFoundError: 文件不存在
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    content = read_file_safe(path, encoding=encoding)
    
    # 统计字符
    total_chars = len(content)
    total_chars_no_spaces = len(content.replace(" ", "").replace("\n", "").replace("\t", ""))
    
    # 提取单词（简单的单词分割）
    words = re.findall(r'\b\w+\b', content.lower())
    total_words = len(words)
    unique_words = len(set(words))
    
    # 统计单词频率
    word_freq = Counter(words)
    top_words = dict(word_freq.most_common(10))
    
    return {
        "total_words": total_words,
        "unique_words": unique_words,
        "total_chars": total_chars,
        "total_chars_no_spaces": total_chars_no_spaces,
        "word_frequency": top_words,
    }

