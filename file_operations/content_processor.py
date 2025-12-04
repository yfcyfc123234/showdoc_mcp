"""
文件内容处理工具
"""

import re
from pathlib import Path
from typing import List, Optional, Callable, Pattern, Literal
import chardet

from .exceptions import FileOperationError, EncodingError
from .safe_writer import SafeFileWriter


def read_file_safe(
    file_path: str | Path,
    encoding: Optional[str] = None,
    errors: str = "strict",
) -> str:
    """
    安全读取文件，自动检测编码
    
    Args:
        file_path: 文件路径
        encoding: 指定编码（如果为 None 则自动检测）
        errors: 错误处理方式（strict, ignore, replace）
    
    Returns:
        文件内容
    
    Raises:
        FileNotFoundError: 文件不存在
        EncodingError: 编码错误
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    if not path.is_file():
        raise FileOperationError(f"路径不是文件: {path}")
    
    # 自动检测编码
    if encoding is None:
        try:
            with open(path, "rb") as f:
                raw_data = f.read()
                detected = chardet.detect(raw_data)
                encoding = detected.get("encoding", "utf-8")
                if encoding is None:
                    encoding = "utf-8"
        except Exception:
            encoding = "utf-8"
    
    try:
        return path.read_text(encoding=encoding, errors=errors)
    except UnicodeDecodeError as e:
        raise EncodingError(f"文件编码错误: {e}")
    except Exception as e:
        raise FileOperationError(f"读取文件失败: {e}")


def write_file_safe(
    file_path: str | Path,
    content: str,
    encoding: str = "utf-8",
    backup: bool = True,
) -> Path:
    """
    安全写入文件
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 文件编码
        backup: 是否备份原文件
    
    Returns:
        文件路径
    
    Raises:
        FileOperationError: 写入失败
    """
    writer = SafeFileWriter(file_path, encoding=encoding, backup=backup)
    writer.write(content)
    return Path(file_path)


def replace_content(
    file_path: str | Path,
    old_text: str | Pattern,
    new_text: str,
    count: int = 0,
    regex: bool = False,
) -> int:
    """
    替换文件内容
    
    Args:
        file_path: 文件路径
        old_text: 要替换的文本或正则表达式
        new_text: 替换后的文本
        count: 替换次数（0 表示全部替换）
        regex: 是否使用正则表达式
    
    Returns:
        替换次数
    
    Raises:
        FileNotFoundError: 文件不存在
        FileOperationError: 替换失败
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    # 读取内容
    content = read_file_safe(path)
    
    # 执行替换
    if regex:
        if isinstance(old_text, str):
            pattern = re.compile(old_text)
        else:
            pattern = old_text
        new_content, replace_count = pattern.subn(new_text, content, count=count)
    else:
        if count == 0:
            new_content = content.replace(old_text, new_text)
            replace_count = content.count(old_text)
        else:
            new_content = content.replace(old_text, new_text, count)
            replace_count = min(count, content.count(old_text))
    
    # 写入文件
    if replace_count > 0:
        writer = SafeFileWriter(path, backup=True)
        writer.write(new_content)
    
    return replace_count


def merge_files(
    file_paths: List[str | Path],
    output_path: str | Path,
    separator: str = "\n",
    encoding: str = "utf-8",
) -> Path:
    """
    合并多个文件
    
    Args:
        file_paths: 要合并的文件路径列表
        output_path: 输出文件路径
        separator: 文件之间的分隔符
        encoding: 文件编码
    
    Returns:
        输出文件路径
    
    Raises:
        FileNotFoundError: 源文件不存在
        FileOperationError: 合并失败
    """
    output = Path(output_path)
    contents = []
    
    for file_path in file_paths:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")
        content = read_file_safe(path, encoding=encoding)
        contents.append(content)
    
    # 写入合并后的内容
    merged_content = separator.join(contents)
    writer = SafeFileWriter(output, encoding=encoding, backup=False)
    writer.write(merged_content)
    
    return output


def split_file(
    file_path: str | Path,
    output_dir: str | Path,
    split_by: Literal["lines", "size", "pattern"] = "lines",
    split_value: int | str = 1000,
    encoding: str = "utf-8",
) -> List[Path]:
    """
    分割文件
    
    Args:
        file_path: 源文件路径
        output_dir: 输出目录
        split_by: 分割方式（lines: 按行数, size: 按大小, pattern: 按模式）
        split_value: 分割值（行数、字节数或正则表达式）
        encoding: 文件编码
    
    Returns:
        分割后的文件路径列表
    
    Raises:
        FileNotFoundError: 源文件不存在
        FileOperationError: 分割失败
    """
    path = Path(file_path)
    output = Path(output_dir)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    output.mkdir(parents=True, exist_ok=True)
    
    content = read_file_safe(path, encoding=encoding)
    output_files = []
    
    if split_by == "lines":
        lines = content.splitlines(keepends=True)
        chunk_size = int(split_value)
        base_name = path.stem
        extension = path.suffix
        
        for i in range(0, len(lines), chunk_size):
            chunk = lines[i:i + chunk_size]
            chunk_content = "".join(chunk)
            output_file = output / f"{base_name}_part{i // chunk_size + 1}{extension}"
            writer = SafeFileWriter(output_file, encoding=encoding, backup=False)
            writer.write(chunk_content)
            output_files.append(output_file)
    
    elif split_by == "size":
        size_limit = int(split_value)
        base_name = path.stem
        extension = path.suffix
        content_bytes = content.encode(encoding)
        
        part_num = 1
        offset = 0
        while offset < len(content_bytes):
            chunk_bytes = content_bytes[offset:offset + size_limit]
            chunk_content = chunk_bytes.decode(encoding, errors="replace")
            output_file = output / f"{base_name}_part{part_num}{extension}"
            writer = SafeFileWriter(output_file, encoding=encoding, backup=False)
            writer.write(chunk_content)
            output_files.append(output_file)
            offset += size_limit
            part_num += 1
    
    elif split_by == "pattern":
        pattern = re.compile(str(split_value))
        parts = pattern.split(content)
        base_name = path.stem
        extension = path.suffix
        
        for i, part in enumerate(parts, 1):
            if part.strip():  # 跳过空部分
                output_file = output / f"{base_name}_part{i}{extension}"
                writer = SafeFileWriter(output_file, encoding=encoding, backup=False)
                writer.write(part)
                output_files.append(output_file)
    
    return output_files


def append_to_file(
    file_path: str | Path,
    content: str,
    encoding: str = "utf-8",
) -> Path:
    """
    追加内容到文件
    
    Args:
        file_path: 文件路径
        content: 要追加的内容
        encoding: 文件编码
    
    Returns:
        文件路径
    
    Raises:
        FileOperationError: 追加失败
    """
    writer = SafeFileWriter(Path(file_path), encoding=encoding, backup=False)
    writer.write(content, mode="append")
    return Path(file_path)


def insert_lines(
    file_path: str | Path,
    lines: List[str],
    line_number: int,
    encoding: str = "utf-8",
) -> Path:
    """
    在指定行号插入多行内容
    
    Args:
        file_path: 文件路径
        lines: 要插入的行列表
        content: 要插入的内容
        line_number: 行号（从1开始）
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
    content = "\n".join(lines)
    writer.insert_lines(content, line_number)
    
    return path


def delete_lines(
    file_path: str | Path,
    start_line: int,
    end_line: Optional[int] = None,
    encoding: str = "utf-8",
) -> Path:
    """
    删除指定行范围的内容
    
    Args:
        file_path: 文件路径
        start_line: 起始行号（从1开始）
        end_line: 结束行号（如果为 None 则只删除一行）
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
    
    content = read_file_safe(path, encoding=encoding)
    lines = content.splitlines(keepends=True)
    
    if end_line is None:
        end_line = start_line
    
    # 调整索引（从1开始转为从0开始）
    start_idx = max(0, start_line - 1)
    end_idx = min(len(lines), end_line)
    
    # 删除指定范围的行
    new_lines = lines[:start_idx] + lines[end_idx:]
    new_content = "".join(new_lines)
    
    writer = SafeFileWriter(path, encoding=encoding, backup=True)
    writer.write(new_content)
    
    return path

