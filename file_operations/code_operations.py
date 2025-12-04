"""
代码块操作工具

提供在代码文件中插入、替换、删除、提取代码块的功能。
"""

import re
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

from .exceptions import FileOperationError
from .content_processor import read_file_safe
from .safe_writer import SafeFileWriter


def find_code_block(
    file_path: str | Path,
    marker: Optional[str] = None,
    function_name: Optional[str] = None,
    class_name: Optional[str] = None,
    line_range: Optional[Tuple[int, int]] = None,
) -> Optional[Dict[str, Any]]:
    """
    查找代码块
    
    Args:
        file_path: 文件路径
        marker: 标记字符串（如 "# MARKER_START" 和 "# MARKER_END"）
        function_name: 函数名
        class_name: 类名
        line_range: 行号范围 (start_line, end_line)
    
    Returns:
        代码块信息字典，包含：
        - start_line: 起始行号
        - end_line: 结束行号
        - content: 代码内容
        如果未找到则返回 None
    
    Raises:
        FileNotFoundError: 文件不存在
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    content = read_file_safe(path)
    lines = content.splitlines(keepends=True)
    
    # 按行号范围查找
    if line_range:
        start_line, end_line = line_range
        if 1 <= start_line <= len(lines) and 1 <= end_line <= len(lines):
            start_idx = start_line - 1
            end_idx = end_line
            block_content = "".join(lines[start_idx:end_idx])
            return {
                "start_line": start_line,
                "end_line": end_line,
                "content": block_content,
            }
        return None
    
    # 按标记查找
    if marker:
        start_marker = f"# {marker}_START"
        end_marker = f"# {marker}_END"
        
        start_line = None
        end_line = None
        
        for i, line in enumerate(lines, 1):
            if start_marker in line:
                start_line = i + 1  # 标记后的下一行
            elif end_marker in line and start_line is not None:
                end_line = i - 1  # 标记前的上一行
                break
        
        if start_line and end_line:
            start_idx = start_line - 1
            end_idx = end_line
            block_content = "".join(lines[start_idx:end_idx])
            return {
                "start_line": start_line,
                "end_line": end_line,
                "content": block_content,
            }
        return None
    
    # 按函数名查找
    if function_name:
        # 简单的函数查找（支持 Python、JavaScript、Kotlin、Dart 等）
        patterns = [
            rf"def\s+{re.escape(function_name)}\s*\(",
            rf"function\s+{re.escape(function_name)}\s*\(",
            rf"fun\s+{re.escape(function_name)}\s*\(",
            rf"{re.escape(function_name)}\s*\([^)]*\)\s*{{",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                start_pos = match.start()
                start_line = content[:start_pos].count("\n") + 1
                
                # 查找函数结束位置（简单实现，查找匹配的大括号或缩进）
                # 这里使用简化版本，实际应该使用 AST 解析
                end_line = _find_function_end(content, start_pos)
                
                if end_line:
                    start_idx = start_line - 1
                    end_idx = end_line
                    block_content = "".join(lines[start_idx:end_idx])
                    return {
                        "start_line": start_line,
                        "end_line": end_line,
                        "content": block_content,
                    }
        return None
    
    # 按类名查找
    if class_name:
        pattern = rf"class\s+{re.escape(class_name)}"
        match = re.search(pattern, content)
        if match:
            start_pos = match.start()
            start_line = content[:start_pos].count("\n") + 1
            
            # 查找类结束位置
            end_line = _find_class_end(content, start_pos)
            
            if end_line:
                start_idx = start_line - 1
                end_idx = end_line
                block_content = "".join(lines[start_idx:end_idx])
                return {
                    "start_line": start_line,
                    "end_line": end_line,
                    "content": block_content,
                }
        return None
    
    return None


def _find_function_end(content: str, start_pos: int) -> Optional[int]:
    """查找函数结束行号（简化实现）"""
    # 这是一个简化实现，实际应该使用 AST
    lines = content.splitlines(keepends=True)
    start_line = content[:start_pos].count("\n")
    
    # 查找第一个非空行的缩进
    if start_line >= len(lines):
        return None
    
    base_indent = len(lines[start_line]) - len(lines[start_line].lstrip())
    brace_count = 0
    paren_count = 0
    
    for i in range(start_line, len(lines)):
        line = lines[i]
        for char in line:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
            elif char == "(":
                paren_count += 1
            elif char == ")":
                paren_count -= 1
        
        # 如果大括号和括号都匹配，且缩进回到基础缩进，可能是函数结束
        if i > start_line and brace_count == 0 and paren_count == 0:
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= base_indent and line.strip():
                return i + 1
    
    return len(lines)


def _find_class_end(content: str, start_pos: int) -> Optional[int]:
    """查找类结束行号（简化实现）"""
    return _find_function_end(content, start_pos)


def insert_code_block(
    file_path: str | Path,
    code: str,
    position: Optional[int] = None,
    line_number: Optional[int] = None,
    marker: Optional[str] = None,
    after_function: Optional[str] = None,
    encoding: str = "utf-8",
) -> Path:
    """
    在文件中插入代码块
    
    Args:
        file_path: 文件路径
        code: 要插入的代码
        position: 字符位置（如果指定）
        line_number: 行号（从1开始，如果指定）
        marker: 标记位置（在标记后插入，如果指定）
        after_function: 函数名（在函数后插入，如果指定）
        encoding: 文件编码
    
    Returns:
        文件路径
    
    Raises:
        FileNotFoundError: 文件不存在
        FileOperationError: 插入失败
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    writer = SafeFileWriter(path, encoding=encoding, backup=True)
    
    if line_number:
        writer.insert_lines(code, line_number)
    elif marker:
        # 在标记后插入
        block_info = find_code_block(path, marker=marker)
        if block_info:
            writer.insert_lines(code, block_info["end_line"] + 1)
        else:
            raise FileOperationError(f"未找到标记: {marker}")
    elif after_function:
        # 在函数后插入
        block_info = find_code_block(path, function_name=after_function)
        if block_info:
            writer.insert_lines(code, block_info["end_line"] + 1)
        else:
            raise FileOperationError(f"未找到函数: {after_function}")
    elif position is not None:
        writer.insert(code, position)
    else:
        # 默认追加到文件末尾
        content = read_file_safe(path, encoding=encoding)
        writer.write(content + "\n" + code)
    
    return path


def replace_code_block(
    file_path: str | Path,
    new_code: str,
    marker: Optional[str] = None,
    function_name: Optional[str] = None,
    class_name: Optional[str] = None,
    line_range: Optional[Tuple[int, int]] = None,
    encoding: str = "utf-8",
) -> Path:
    """
    替换代码块
    
    Args:
        file_path: 文件路径
        new_code: 新代码
        marker: 标记字符串
        function_name: 函数名
        class_name: 类名
        line_range: 行号范围
        encoding: 文件编码
    
    Returns:
        文件路径
    
    Raises:
        FileNotFoundError: 文件不存在
        FileOperationError: 替换失败
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    # 查找代码块
    block_info = find_code_block(
        path,
        marker=marker,
        function_name=function_name,
        class_name=class_name,
        line_range=line_range,
    )
    
    if not block_info:
        raise FileOperationError("未找到要替换的代码块")
    
    # 读取文件内容
    content = read_file_safe(path, encoding=encoding)
    lines = content.splitlines(keepends=True)
    
    # 替换代码块
    start_idx = block_info["start_line"] - 1
    end_idx = block_info["end_line"]
    
    new_lines = lines[:start_idx] + [new_code + "\n" if not new_code.endswith("\n") else new_code] + lines[end_idx:]
    new_content = "".join(new_lines)
    
    # 写入文件
    writer = SafeFileWriter(path, encoding=encoding, backup=True)
    writer.write(new_content)
    
    return path


def delete_code_block(
    file_path: str | Path,
    marker: Optional[str] = None,
    function_name: Optional[str] = None,
    class_name: Optional[str] = None,
    line_range: Optional[Tuple[int, int]] = None,
    encoding: str = "utf-8",
) -> Path:
    """
    删除代码块
    
    Args:
        file_path: 文件路径
        marker: 标记字符串
        function_name: 函数名
        class_name: 类名
        line_range: 行号范围
        encoding: 文件编码
    
    Returns:
        文件路径
    
    Raises:
        FileNotFoundError: 文件不存在
        FileOperationError: 删除失败
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    # 查找代码块
    block_info = find_code_block(
        path,
        marker=marker,
        function_name=function_name,
        class_name=class_name,
        line_range=line_range,
    )
    
    if not block_info:
        raise FileOperationError("未找到要删除的代码块")
    
    # 使用 content_processor 的 delete_lines
    from .content_processor import delete_lines
    return delete_lines(path, block_info["start_line"], block_info["end_line"], encoding=encoding)


def extract_code_block(
    file_path: str | Path,
    output_path: str | Path,
    marker: Optional[str] = None,
    function_name: Optional[str] = None,
    class_name: Optional[str] = None,
    line_range: Optional[Tuple[int, int]] = None,
    encoding: str = "utf-8",
) -> Path:
    """
    提取代码块到新文件
    
    Args:
        file_path: 源文件路径
        output_path: 输出文件路径
        marker: 标记字符串
        function_name: 函数名
        class_name: 类名
        line_range: 行号范围
        encoding: 文件编码
    
    Returns:
        输出文件路径
    
    Raises:
        FileNotFoundError: 源文件不存在
        FileOperationError: 提取失败
    """
    path = Path(file_path)
    output = Path(output_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    # 查找代码块
    block_info = find_code_block(
        path,
        marker=marker,
        function_name=function_name,
        class_name=class_name,
        line_range=line_range,
    )
    
    if not block_info:
        raise FileOperationError("未找到要提取的代码块")
    
    # 写入新文件
    writer = SafeFileWriter(output, encoding=encoding, backup=False)
    writer.write(block_info["content"])
    
    return output

