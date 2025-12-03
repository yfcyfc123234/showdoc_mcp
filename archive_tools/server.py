"""
压缩解压核心功能实现

支持 ZIP、7Z、RAR 格式的压缩和解压。
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# 尝试导入 zipfile（标准库）
try:
    import zipfile
    HAS_ZIPFILE = True
except ImportError:
    HAS_ZIPFILE = False
    logger.warning("zipfile 未安装，ZIP 格式将不可用")

# 尝试导入 pyzipper（支持真正的密码保护）
try:
    import pyzipper
    HAS_PYZIPPER = True
except ImportError:
    HAS_PYZIPPER = False
    logger.warning("pyzipper 未安装，ZIP 格式将使用标准库（密码保护有限）")

# 尝试导入可选依赖
try:
    import py7zr
    HAS_PY7ZR = True
except ImportError:
    HAS_PY7ZR = False
    logger.warning("py7zr 未安装，7Z 格式将不可用")

try:
    import rarfile
    HAS_RARFILE = True
except ImportError:
    HAS_RARFILE = False
    logger.warning("rarfile 未安装，RAR 格式将不可用")


def _parse_size(size_str: str) -> int:
    """
    解析大小字符串（如 "100MB", "1GB"）为字节数。
    
    Args:
        size_str: 大小字符串，支持 B, KB, MB, GB, TB
        
    Returns:
        字节数
    """
    size_str = size_str.strip().upper()
    
    # 提取数字和单位
    if size_str.endswith("B"):
        unit = size_str[-2:]
        number = size_str[:-2]
    elif size_str.endswith("K"):
        unit = "KB"
        number = size_str[:-1]
    elif size_str.endswith("M"):
        unit = "MB"
        number = size_str[:-1]
    elif size_str.endswith("G"):
        unit = "GB"
        number = size_str[:-1]
    elif size_str.endswith("T"):
        unit = "TB"
        number = size_str[:-1]
    else:
        # 默认字节
        return int(size_str)
    
    number = float(number)
    
    multipliers = {
        "B": 1,
        "KB": 1024,
        "MB": 1024 ** 2,
        "GB": 1024 ** 3,
        "TB": 1024 ** 4,
    }
    
    return int(number * multipliers.get(unit, 1))


def _validate_format(format: str) -> bool:
    """
    验证格式是否支持。
    
    Args:
        format: 压缩格式（zip, 7z, rar）
        
    Returns:
        是否支持
    """
    format_lower = format.lower()
    
    if format_lower == "zip":
        return HAS_ZIPFILE or HAS_PYZIPPER
    elif format_lower == "7z":
        return HAS_PY7ZR
    elif format_lower == "rar":
        return HAS_RARFILE
    else:
        return False


def _get_zip_compression_method(level: int) -> int:
    """
    获取 ZIP 压缩方法。
    
    Args:
        level: 压缩级别（0-9）
        
    Returns:
        zipfile 压缩方法常量
    """
    if HAS_ZIPFILE:
        if level == 0:
            return zipfile.ZIP_STORED
        else:
            return zipfile.ZIP_DEFLATED
    elif HAS_PYZIPPER:
        if level == 0:
            return pyzipper.ZIP_STORED
        else:
            return pyzipper.ZIP_DEFLATED
    else:
        # 默认值
        return 8  # ZIP_DEFLATED


def _collect_files(source_paths: List[str]) -> List[Path]:
    """
    收集所有要压缩的文件。
    
    Args:
        source_paths: 源文件/目录路径列表
        
    Returns:
        文件路径列表
    """
    files = []
    
    for source_path in source_paths:
        path = Path(source_path)
        
        if not path.exists():
            raise FileNotFoundError(f"文件或目录不存在: {source_path}")
        
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            # 递归收集目录中的所有文件
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    files.append(file_path)
    
    return files


def compress_files(
    source_paths: List[str],
    output_path: str,
    format: str = "zip",
    compression_level: int = 6,
    compression_method: str = "standard",
    password: Optional[str] = None,
    split_size: Optional[str] = None,
    delete_source: bool = False,
    store_low_ratio: bool = False,
    separate_archives: bool = False,
) -> Dict[str, Any]:
    """
    压缩文件或目录。
    
    Args:
        source_paths: 源文件/目录路径列表
        output_path: 输出压缩文件路径
        format: 压缩格式（zip, 7z, rar），默认 zip
        compression_level: 压缩级别（0-9），0=最快，9=最小，默认 6
        compression_method: 压缩方式（standard, store, fastest, best），默认 standard
        password: 压缩密码（可选）
        split_size: 分卷大小（如 "100MB", "1GB"），None 表示不分卷
        delete_source: 压缩后删除源文件，默认 False
        store_low_ratio: 直接存储压缩率低的文件，默认 False
        separate_archives: 压缩每个文件到单独的压缩包，默认 False
        
    Returns:
        压缩结果字典
    """
    try:
        # 验证格式
        if not _validate_format(format):
            available_formats = []
            if HAS_ZIPFILE or HAS_PYZIPPER:
                available_formats.append("zip")
            if HAS_PY7ZR:
                available_formats.append("7z")
            if HAS_RARFILE:
                available_formats.append("rar")
            
            return {
                "ok": False,
                "error": f"不支持的格式: {format}。可用格式: {', '.join(available_formats) if available_formats else '无'}",
            }
        
        # 验证压缩级别
        compression_level = max(0, min(9, compression_level))
        
        # 收集文件
        try:
            files = _collect_files(source_paths)
        except FileNotFoundError as e:
            return {
                "ok": False,
                "error": str(e),
            }
        
        if not files:
            return {
                "ok": False,
                "error": "没有找到要压缩的文件",
            }
        
        output_path_obj = Path(output_path)
        output_dir = output_path_obj.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 处理每个文件单独压缩的情况
        if separate_archives:
            created_archives = []
            for file_path in files:
                archive_name = output_path_obj.stem + "_" + file_path.stem + output_path_obj.suffix
                archive_path = output_dir / archive_name
                
                result = _compress_single_file(
                    file_path,
                    str(archive_path),
                    format,
                    compression_level,
                    password,
                )
                
                if not result.get("ok"):
                    return result
                
                created_archives.append(str(archive_path))
            
            # 删除源文件
            if delete_source:
                for source_path in source_paths:
                    path = Path(source_path)
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        shutil.rmtree(path)
            
            return {
                "ok": True,
                "output_paths": created_archives,
                "message": f"成功创建 {len(created_archives)} 个压缩包",
            }
        
        # 处理分卷压缩
        # 注意：ZIP 格式的分卷压缩需要使用外部工具，这里不支持
        if split_size and format.lower() == "zip":
            return {
                "ok": False,
                "error": "ZIP 格式的分卷压缩需要使用外部工具。建议使用 7Z 格式进行分卷压缩。",
            }
        
        if split_size:
            split_size_bytes = _parse_size(split_size)
            return _compress_with_split(
                files,
                output_path,
                format,
                compression_level,
                password,
                split_size_bytes,
                delete_source,
            )
        
        # 普通压缩
        result = _compress_files_internal(
            files,
            output_path,
            format,
            compression_level,
            password,
        )
        
        if not result.get("ok"):
            return result
        
        # 删除源文件
        if delete_source:
            try:
                for source_path in source_paths:
                    path = Path(source_path)
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        shutil.rmtree(path)
            except Exception as e:
                logger.warning(f"删除源文件失败: {e}")
        
        return {
            "ok": True,
            "output_path": result["output_path"],
            "message": "压缩成功",
        }
        
    except Exception as e:
        logger.exception("压缩失败")
        return {
            "ok": False,
            "error": f"压缩失败: {str(e)}",
        }


def _compress_single_file(
    file_path: Path,
    output_path: str,
    format: str,
    compression_level: int,
    password: Optional[str],
) -> Dict[str, Any]:
    """压缩单个文件（内部函数）。"""
    format_lower = format.lower()
    
    if format_lower == "zip":
        return _compress_zip([file_path], output_path, compression_level, password)
    elif format_lower == "7z":
        return _compress_7z([file_path], output_path, compression_level, password)
    elif format_lower == "rar":
        return _compress_rar([file_path], output_path, compression_level, password)
    else:
        return {
            "ok": False,
            "error": f"不支持的格式: {format}",
        }


def _compress_files_internal(
    files: List[Path],
    output_path: str,
    format: str,
    compression_level: int,
    password: Optional[str],
) -> Dict[str, Any]:
    """压缩文件列表（内部函数）。"""
    format_lower = format.lower()
    
    if format_lower == "zip":
        return _compress_zip(files, output_path, compression_level, password)
    elif format_lower == "7z":
        return _compress_7z(files, output_path, compression_level, password)
    elif format_lower == "rar":
        return _compress_rar(files, output_path, compression_level, password)
    else:
        return {
            "ok": False,
            "error": f"不支持的格式: {format}",
        }


def _compress_zip(
    files: List[Path],
    output_path: str,
    compression_level: int,
    password: Optional[str],
) -> Dict[str, Any]:
    """压缩为 ZIP 格式。
    
    如果安装了 pyzipper，使用 pyzipper 提供真正的 AES 密码保护。
    否则使用标准库 zipfile（密码保护有限）。
    """
    try:
        compression = _get_zip_compression_method(compression_level)
        
        # 如果安装了 pyzipper，优先使用 pyzipper（支持真正的密码保护）
        if HAS_PYZIPPER:
            # 如果设置了密码，使用 AES 加密
            if password:
                with pyzipper.AESZipFile(
                    output_path,
                    "w",
                    compression=compression,
                    compresslevel=compression_level if compression_level > 0 else None,
                    encryption=pyzipper.WZ_AES,  # 使用 AES 加密
                ) as zipf:
                    zipf.setpassword(password.encode("utf-8"))
                    
                    # 添加文件
                    for file_path in files:
                        arcname = file_path.name
                        zipf.write(file_path, arcname)
            else:
                # 没有密码时，使用普通的 ZipFile
                with pyzipper.ZipFile(
                    output_path,
                    "w",
                    compression=compression,
                    compresslevel=compression_level if compression_level > 0 else None,
                ) as zipf:
                    # 添加文件
                    for file_path in files:
                        arcname = file_path.name
                        zipf.write(file_path, arcname)
        else:
            # 使用标准库 zipfile（如果没有 pyzipper）
            if not HAS_ZIPFILE:
                return {
                    "ok": False,
                    "error": "zipfile 未安装，无法使用 ZIP 格式。建议安装 pyzipper: pip install pyzipper",
                }
            
            with zipfile.ZipFile(
                output_path,
                "w",
                compression=compression,
                compresslevel=compression_level if compression_level > 0 else None,
            ) as zipf:
                # 设置密码（如果提供）
                # 注意：标准库 zipfile 的加密支持有限
                if password:
                    zipf.setpassword(password.encode("utf-8"))
                
                # 添加文件
                for file_path in files:
                    arcname = file_path.name
                    zipf.write(file_path, arcname)
        
        return {
            "ok": True,
            "output_path": output_path,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"ZIP 压缩失败: {str(e)}",
        }


def _compress_7z(
    files: List[Path],
    output_path: str,
    compression_level: int,
    password: Optional[str],
) -> Dict[str, Any]:
    """压缩为 7Z 格式。"""
    if not HAS_PY7ZR:
        return {
            "ok": False,
            "error": "py7zr 未安装，无法使用 7Z 格式",
        }
    
    try:
        # py7zr 的压缩级别映射
        # 0=store, 1=fastest, 5=normal, 9=ultra
        if compression_level == 0:
            filters = [{"id": py7zr.FILTER_COPY}]
        elif compression_level <= 3:
            filters = [{"id": py7zr.FILTER_LZMA2, "preset": 1}]
        elif compression_level <= 6:
            filters = [{"id": py7zr.FILTER_LZMA2, "preset": 5}]
        else:
            filters = [{"id": py7zr.FILTER_LZMA2, "preset": 9}]
        
        with py7zr.SevenZipFile(
            output_path,
            "w",
            filters=filters,
            password=password,
        ) as archive:
            for file_path in files:
                archive.write(file_path, file_path.name)
        
        return {
            "ok": True,
            "output_path": output_path,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"7Z 压缩失败: {str(e)}",
        }


def _compress_rar(
    files: List[Path],
    output_path: str,
    compression_level: int,
    password: Optional[str],
) -> Dict[str, Any]:
    """压缩为 RAR 格式。"""
    if not HAS_RARFILE:
        return {
            "ok": False,
            "error": "rarfile 未安装，无法使用 RAR 格式",
        }
    
    try:
        # rarfile 不支持直接创建 RAR 文件（需要外部工具）
        # 这里返回错误，提示用户使用其他格式或安装 WinRAR/rar 工具
        return {
            "ok": False,
            "error": "RAR 格式创建需要系统安装 WinRAR 或 rar 工具，建议使用 ZIP 或 7Z 格式",
        }
    except Exception as e:
        return {
            "ok": False,
            "error": f"RAR 压缩失败: {str(e)}",
        }


def _compress_with_split(
    files: List[Path],
    output_path: str,
    format: str,
    compression_level: int,
    password: Optional[str],
    split_size_bytes: int,
    delete_source: bool,
) -> Dict[str, Any]:
    """分卷压缩。"""
    format_lower = format.lower()
    
    # 7Z 格式支持分卷压缩
    if format_lower == "7z" and HAS_PY7ZR:
        # 注意：py7zr 库本身不支持分卷压缩（volume_size 参数不存在）
        # 需要使用外部工具（如 7z.exe）或手动分割文件
        # 这里我们返回错误，提示用户使用外部工具
        return {
            "ok": False,
            "error": "py7zr 库不支持分卷压缩。如需分卷压缩，请使用外部 7z 工具（如 7z.exe）或手动分割文件。",
        }
    
    # ZIP 格式的分卷压缩（zipfile 不支持真正的分卷，这里给出提示）
    if format_lower == "zip":
        return {
            "ok": False,
            "error": "ZIP 格式的分卷压缩需要使用外部工具。建议使用 7Z 格式进行分卷压缩，或使用 WinRAR 等工具创建 ZIP 分卷。",
        }
    
    # RAR 格式需要外部工具
    if format_lower == "rar":
        return {
            "ok": False,
            "error": "RAR 格式的分卷压缩需要系统安装 WinRAR 或 rar 工具。建议使用 7Z 格式进行分卷压缩。",
        }
    
    return {
        "ok": False,
        "error": f"分卷压缩目前仅支持 7Z 格式（需要 py7zr）。当前格式: {format}",
    }


def extract_archive(
    archive_path: str,
    output_dir: Optional[str] = None,
    password: Optional[str] = None,
    delete_archive: bool = False,
) -> Dict[str, Any]:
    """
    解压压缩文件。
    
    Args:
        archive_path: 压缩文件路径
        output_dir: 输出目录，None 表示解压到压缩文件所在目录
        password: 解压密码（可选）
        delete_archive: 解压后删除压缩包，默认 False
        
    Returns:
        解压结果字典
    """
    try:
        archive_path_obj = Path(archive_path)
        
        if not archive_path_obj.exists():
            return {
                "ok": False,
                "error": f"压缩文件不存在: {archive_path}",
            }
        
        # 确定输出目录
        if output_dir is None:
            output_dir = archive_path_obj.parent / archive_path_obj.stem
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 根据文件扩展名判断格式
        ext = archive_path_obj.suffix.lower()
        
        if ext == ".zip":
            result = _extract_zip(archive_path, output_dir, password)
        elif ext == ".7z":
            result = _extract_7z(archive_path, output_dir, password)
        elif ext in [".rar", ".r00"]:
            result = _extract_rar(archive_path, output_dir, password)
        else:
            # 尝试自动检测格式
            result = _extract_auto(archive_path, output_dir, password)
        
        if not result.get("ok"):
            return result
        
        # 删除压缩包
        if delete_archive:
            try:
                archive_path_obj.unlink()
            except Exception as e:
                logger.warning(f"删除压缩包失败: {e}")
        
        return {
            "ok": True,
            "output_dir": str(output_dir),
            "extracted_files": result.get("extracted_files", []),
            "message": "解压成功",
        }
        
    except Exception as e:
        logger.exception("解压失败")
        return {
            "ok": False,
            "error": f"解压失败: {str(e)}",
        }


def _extract_zip(
    archive_path: str,
    output_dir: Path,
    password: Optional[str],
) -> Dict[str, Any]:
    """解压 ZIP 格式。
    
    如果安装了 pyzipper，优先使用 pyzipper 提供真正的密码保护。
    否则使用标准库 zipfile（密码保护有限）。
    """
    try:
        extracted_files = []
        
        # 优先尝试使用 pyzipper（如果已安装）
        if HAS_PYZIPPER:
            try:
                # 尝试使用 AESZipFile（支持加密的 ZIP）
                with pyzipper.AESZipFile(archive_path, "r") as zipf:
                    if password:
                        zipf.setpassword(password.encode("utf-8"))
                    
                    # 解压所有文件
                    zipf.extractall(output_dir)
                    
                    # 获取解压的文件列表
                    for name in zipf.namelist():
                        extracted_files.append(name)
                
                return {
                    "ok": True,
                    "extracted_files": extracted_files,
                }
            except (pyzipper.BadZipFile, ValueError):
                # 如果不是 AES 加密的 ZIP，尝试普通 ZipFile
                try:
                    with pyzipper.ZipFile(archive_path, "r") as zipf:
                        if password:
                            zipf.setpassword(password.encode("utf-8"))
                        
                        zipf.extractall(output_dir)
                        
                        for name in zipf.namelist():
                            extracted_files.append(name)
                    
                    return {
                        "ok": True,
                        "extracted_files": extracted_files,
                    }
                except RuntimeError as e:
                    error_msg = str(e).lower()
                    if "bad password" in error_msg or "password" in error_msg or "decryption" in error_msg:
                        return {
                            "ok": False,
                            "error": "密码错误",
                        }
                    raise
            except RuntimeError as e:
                error_msg = str(e).lower()
                if "bad password" in error_msg or "password" in error_msg or "decryption" in error_msg:
                    return {
                        "ok": False,
                        "error": "密码错误",
                    }
                # 其他错误继续尝试标准库
            except Exception as e:
                error_msg = str(e).lower()
                if "bad password" in error_msg or "password" in error_msg or "decryption" in error_msg:
                    return {
                        "ok": False,
                        "error": "密码错误",
                    }
                # 其他错误继续尝试标准库
        
        # 使用标准库 zipfile
        if not HAS_ZIPFILE:
            return {
                "ok": False,
                "error": "zipfile 未安装，无法解压 ZIP 格式",
            }
        
        with zipfile.ZipFile(archive_path, "r") as zipf:
            if password:
                zipf.setpassword(password.encode("utf-8"))
            
            # 解压所有文件
            zipf.extractall(output_dir)
            
            # 获取解压的文件列表
            for name in zipf.namelist():
                extracted_files.append(name)
        
        return {
            "ok": True,
            "extracted_files": extracted_files,
        }
    except zipfile.BadZipFile:
        return {
            "ok": False,
            "error": "ZIP 文件损坏或格式不正确",
        }
    except RuntimeError as e:
        error_msg = str(e).lower()
        if "bad password" in error_msg or ("password" in error_msg and "wrong" in error_msg) or "decryption" in error_msg:
            return {
                "ok": False,
                "error": "密码错误",
            }
        return {
            "ok": False,
            "error": f"ZIP 解压失败: {str(e)}",
        }
    except Exception as e:
        error_msg = str(e).lower()
        if "bad password" in error_msg or ("password" in error_msg and "wrong" in error_msg) or "decryption" in error_msg:
            return {
                "ok": False,
                "error": "密码错误",
            }
        return {
            "ok": False,
            "error": f"ZIP 解压失败: {str(e)}",
        }


def _extract_7z(
    archive_path: str,
    output_dir: Path,
    password: Optional[str],
) -> Dict[str, Any]:
    """解压 7Z 格式。"""
    if not HAS_PY7ZR:
        return {
            "ok": False,
            "error": "py7zr 未安装，无法解压 7Z 格式",
        }
    
    try:
        extracted_files = []
        
        with py7zr.SevenZipFile(archive_path, mode="r", password=password) as archive:
            # 解压所有文件
            # py7zr 在密码错误时，extractall() 会抛出 LZMAError 异常
            archive.extractall(output_dir)
            
            # 获取解压的文件列表
            for file_info in archive.getnames():
                extracted_files.append(file_info)
        
        return {
            "ok": True,
            "extracted_files": extracted_files,
        }
    except py7zr.exceptions.Bad7zFile:
        # 如果提供了密码，Bad7zFile 可能是密码错误导致的
        if password:
            return {
                "ok": False,
                "error": "密码错误",
            }
        return {
            "ok": False,
            "error": "7Z 文件损坏或格式不正确",
        }
    except Exception as e:
        # py7zr 在密码错误时会抛出 LZMAError 异常（来自 _lzma 模块）
        # 错误消息通常是 "Corrupt input data"
        error_type = type(e).__name__
        error_msg = str(e).lower()
        error_module = type(e).__module__
        
        # 检查是否是密码相关的错误
        # py7zr 密码错误通常表现为 LZMAError 或 "Corrupt input data"
        # 如果提供了密码，任何解压错误都可能是密码错误
        if password:
            # LZMAError 通常是密码错误（检查类型名或模块名）
            if (
                "lzma" in error_type.lower() or 
                "lzma" in error_module.lower() or
                error_type == "LZMAError"
            ):
                return {
                    "ok": False,
                    "error": "密码错误",
                }
            # 其他可能的密码错误标识
            if (
                "password" in error_msg or 
                "wrong password" in error_msg or
                "corrupt" in error_msg or
                "decrypt" in error_msg or
                "bad" in error_msg
            ):
                return {
                    "ok": False,
                    "error": "密码错误",
                }
            # 如果提供了密码但解压失败，且错误消息包含 "corrupt"，很可能是密码错误
            if "corrupt" in error_msg:
                return {
                    "ok": False,
                    "error": "密码错误",
                }
        
        return {
            "ok": False,
            "error": f"7Z 解压失败: {str(e)}",
        }


def _extract_rar(
    archive_path: str,
    output_dir: Path,
    password: Optional[str],
) -> Dict[str, Any]:
    """解压 RAR 格式。"""
    if not HAS_RARFILE:
        return {
            "ok": False,
            "error": "rarfile 未安装，无法解压 RAR 格式",
        }
    
    try:
        # 检查 unrar 工具是否可用
        if not rarfile.UNRAR_TOOL:
            return {
                "ok": False,
                "error": "系统未安装 unrar 工具，无法解压 RAR 格式。请安装 WinRAR 或 unrar 工具。",
            }
        
        extracted_files = []
        
        with rarfile.RarFile(archive_path, "r") as rar:
            if password:
                rar.setpassword(password)
            
            rar.extractall(output_dir)
            
            # 获取解压的文件列表
            for file_info in rar.infolist():
                if not file_info.isdir():
                    extracted_files.append(file_info.filename)
        
        return {
            "ok": True,
            "extracted_files": extracted_files,
        }
    except rarfile.BadRarFile:
        return {
            "ok": False,
            "error": "RAR 文件损坏或格式不正确",
        }
    except rarfile.NeedFirstVolume:
        return {
            "ok": False,
            "error": "需要第一个分卷文件（.rar 或 .part1.rar）",
        }
    except Exception as e:
        error_msg = str(e).lower()
        if "password" in error_msg or "wrong password" in error_msg:
            return {
                "ok": False,
                "error": "密码错误",
            }
        return {
            "ok": False,
            "error": f"RAR 解压失败: {str(e)}",
        }


def _extract_auto(
    archive_path: str,
    output_dir: Path,
    password: Optional[str],
) -> Dict[str, Any]:
    """自动检测格式并解压。"""
    # 尝试 ZIP
    try:
        with zipfile.ZipFile(archive_path, "r") as zipf:
            return _extract_zip(archive_path, output_dir, password)
    except:
        pass
    
    # 尝试 7Z
    if HAS_PY7ZR:
        try:
            with py7zr.SevenZipFile(archive_path, mode="r") as archive:
                return _extract_7z(archive_path, output_dir, password)
        except:
            pass
    
    # 尝试 RAR
    if HAS_RARFILE:
        try:
            return _extract_rar(archive_path, output_dir, password)
        except:
            pass
    
    return {
        "ok": False,
        "error": "无法识别压缩文件格式，请确保文件是 ZIP、7Z 或 RAR 格式",
    }

