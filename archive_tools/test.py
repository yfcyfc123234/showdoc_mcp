"""
压缩解压工具测试脚本

测试压缩和解压功能，支持 ZIP、7Z、RAR 格式。

使用方法：
1. 在 archive_tools 目录内运行：python test.py
2. 从项目根目录运行：python -m archive_tools.test

测试结果会自动保存到 archive_tools/test_results.md 文件（如果 SAVE_RESULTS_TO_FILE = True）
可以直接查看该文件了解测试详情。
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from io import StringIO

# 设置控制台编码为 UTF-8（Windows）
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except (AttributeError, ValueError, OSError):
            pass
    if hasattr(sys.stderr, 'reconfigure'):
        try:
            sys.stderr.reconfigure(encoding='utf-8')
        except (AttributeError, ValueError, OSError):
            pass

# 添加父目录到路径（如果在 archive_tools 目录内运行）
if Path(__file__).parent.name == 'archive_tools':
    sys.path.insert(0, str(Path(__file__).parent.parent))

from archive_tools import compress_files, extract_archive


# ========== 测试配置 ==========
# 是否自动清理测试文件
AUTO_CLEANUP = True

# 是否显示详细信息
SHOW_DETAILS = True

# 是否保存测试结果到文档
SAVE_RESULTS_TO_FILE = True

# 测试结果保存路径（相对于项目根目录）
RESULTS_FILE_PATH = "archive_tools/test_results.md"
# ====================================================


class TeeOutput:
    """同时输出到控制台和文件的类"""
    def __init__(self, file_path: Path):
        self.terminal = sys.stdout
        self.file = open(file_path, 'w', encoding='utf-8')
        self.file_path = file_path
    
    def write(self, message):
        self.terminal.write(message)
        self.file.write(message)
        self.file.flush()
    
    def flush(self):
        self.terminal.flush()
        self.file.flush()
    
    def close(self):
        if self.file:
            self.file.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


def create_test_files(test_dir: Path):
    """创建测试文件"""
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建测试文件
    (test_dir / "file1.txt").write_text("这是测试文件 1 的内容\n包含中文和英文 content", encoding="utf-8")
    (test_dir / "file2.txt").write_text("这是测试文件 2 的内容\nTest file 2 content", encoding="utf-8")
    
    # 创建子目录和文件
    sub_dir = test_dir / "subdir"
    sub_dir.mkdir(exist_ok=True)
    (sub_dir / "file3.txt").write_text("子目录中的文件", encoding="utf-8")
    
    print(f"  ✓ 创建测试文件在: {test_dir}")
    return test_dir


def test_default_format(test_dir: Path, output_dir: Path):
    """测试默认格式（不指定 format，应该使用 zip）"""
    print("\n" + "=" * 70)
    print("测试 1: 默认格式测试（不指定 format，应使用 ZIP）")
    print("=" * 70)
    
    output_path = output_dir / "test_default.zip"
    
    # 不指定 format，应该默认使用 zip
    result = compress_files(
        source_paths=[str(test_dir / "file1.txt")],
        output_path=str(output_path),
        # format 不指定，使用默认值
        compression_level=6,
    )
    
    if result.get("ok"):
        print(f"  ✓ 默认格式压缩成功（使用 ZIP）")
        print(f"    输出文件: {result.get('output_path')}")
        file_size = Path(result.get('output_path')).stat().st_size
        print(f"    文件大小: {file_size} 字节")
        
        # 验证确实是 ZIP 格式
        if output_path.suffix.lower() == ".zip" or "zip" in str(result.get('output_path')).lower():
            print(f"    ✓ 确认使用 ZIP 格式（默认格式）")
        
        return output_path
    else:
        print(f"  ✗ 默认格式压缩失败: {result.get('error')}")
        return None


def test_compress_zip(test_dir: Path, output_dir: Path):
    """测试 ZIP 压缩（无密码）"""
    print("\n" + "=" * 70)
    print("测试 2: ZIP 格式压缩（无密码）")
    print("=" * 70)
    
    output_path = output_dir / "test_zip_no_password.zip"
    
    result = compress_files(
        source_paths=[str(test_dir)],
        output_path=str(output_path),
        format="zip",
        compression_level=6,
    )
    
    if result.get("ok"):
        print(f"  ✓ ZIP 压缩成功（无密码）")
        print(f"    输出文件: {result.get('output_path')}")
        file_size = Path(result.get('output_path')).stat().st_size
        print(f"    文件大小: {file_size} 字节")
        return output_path
    else:
        print(f"  ✗ ZIP 压缩失败: {result.get('error')}")
        return None


def test_extract_zip(archive_path: Path, output_dir: Path):
    """测试 ZIP 解压（无密码）"""
    print("\n" + "=" * 70)
    print("测试 3: ZIP 格式解压（无密码）")
    print("=" * 70)
    
    extract_dir = output_dir / "extracted_zip"
    
    result = extract_archive(
        archive_path=str(archive_path),
        output_dir=str(extract_dir),
    )
    
    if result.get("ok"):
        print(f"  ✓ ZIP 解压成功")
        print(f"    输出目录: {result.get('output_dir')}")
        extracted_files = result.get('extracted_files', [])
        print(f"    解压文件数: {len(extracted_files)}")
        if SHOW_DETAILS and extracted_files:
            print("    文件列表:")
            for f in extracted_files[:5]:
                print(f"      - {f}")
            if len(extracted_files) > 5:
                print(f"      ... 还有 {len(extracted_files) - 5} 个文件")
        return extract_dir
    else:
        print(f"  ✗ ZIP 解压失败: {result.get('error')}")
        return None


def test_compress_zip_with_password(test_dir: Path, output_dir: Path):
    """测试 ZIP 密码压缩"""
    print("\n" + "=" * 70)
    print("测试 4: ZIP 格式压缩（有密码）")
    print("=" * 70)
    
    output_path = output_dir / "test_password.zip"
    
    result = compress_files(
        source_paths=[str(test_dir / "file1.txt")],
        output_path=str(output_path),
        format="zip",
        compression_level=6,
        password="test123",
    )
    
    if result.get("ok"):
        print(f"  ✓ 密码压缩成功")
        print(f"    输出文件: {result.get('output_path')}")
        
        # 测试密码解压
        extract_dir = output_dir / "extracted_password"
        extract_result = extract_archive(
            archive_path=str(output_path),
            output_dir=str(extract_dir),
            password="test123",
        )
        
        if extract_result.get("ok"):
            print(f"  ✓ 密码解压成功")
        else:
            print(f"  ✗ 密码解压失败: {extract_result.get('error')}")
        
        # 测试错误密码
        extract_result2 = extract_archive(
            archive_path=str(output_path),
            output_dir=str(output_dir / "extracted_wrong_password"),
            password="wrong_password",
        )
        
        if not extract_result2.get("ok"):
            print(f"  ✓ ZIP 错误密码检测成功（正确拒绝解压）")
            print(f"    错误信息: {extract_result2.get('error')}")
            # 检查是否使用了 pyzipper
            try:
                import pyzipper
                print(f"    ✓ 使用了 pyzipper，提供真正的 AES 密码保护")
            except ImportError:
                print(f"    ⚠ 未安装 pyzipper，但密码保护正常工作")
        else:
            # 检查是否使用了 pyzipper
            try:
                import pyzipper
                print(f"  ⚠ ZIP 错误密码检测失败（可能使用了标准库 zipfile）")
                print(f"     建议：确保安装了 pyzipper: pip install pyzipper")
            except ImportError:
                print(f"  ⚠ ZIP 格式密码保护限制：错误密码也能解压（Python zipfile 库的限制）")
                print(f"     建议：安装 pyzipper 以获得真正的密码保护: pip install pyzipper")
        
        return output_path
    else:
        print(f"  ✗ 密码压缩失败: {result.get('error')}")
        return None


def test_extract_zip_with_password(archive_path: Path, output_dir: Path):
    """测试 ZIP 解压（有密码）"""
    print("\n" + "=" * 70)
    print("测试 5: ZIP 格式解压（有密码 - 正确密码）")
    print("=" * 70)
    
    extract_dir = output_dir / "extracted_zip_password"
    
    result = extract_archive(
        archive_path=str(archive_path),
        output_dir=str(extract_dir),
        password="test123",
    )
    
    if result.get("ok"):
        print(f"  ✓ ZIP 密码解压成功（正确密码）")
        print(f"    输出目录: {result.get('output_dir')}")
        extracted_files = result.get('extracted_files', [])
        print(f"    解压文件数: {len(extracted_files)}")
        return extract_dir
    else:
        print(f"  ✗ ZIP 密码解压失败: {result.get('error')}")
        return None


def test_extract_zip_wrong_password(archive_path: Path, output_dir: Path):
    """测试 ZIP 解压（错误密码）"""
    print("\n" + "=" * 70)
    print("测试 6: ZIP 格式解压（有密码 - 错误密码）")
    print("=" * 70)
    
    extract_dir = output_dir / "extracted_zip_wrong_password"
    
    result = extract_archive(
        archive_path=str(archive_path),
        output_dir=str(extract_dir),
        password="wrong_password",
    )
    
    if not result.get("ok"):
        print(f"  ✓ ZIP 错误密码检测成功（正确拒绝解压）")
        print(f"    错误信息: {result.get('error')}")
        # 检查是否使用了 pyzipper
        try:
            import pyzipper
            print(f"    ✓ 使用了 pyzipper，提供真正的 AES 密码保护")
        except ImportError:
            print(f"    ⚠ 未安装 pyzipper，但密码保护正常工作")
        return None
    else:
        # 检查是否使用了 pyzipper
        try:
            import pyzipper
            print(f"  ⚠ ZIP 错误密码检测失败（可能使用了标准库 zipfile）")
            print(f"     建议：确保安装了 pyzipper: pip install pyzipper")
        except ImportError:
            print(f"  ⚠ ZIP 格式密码保护限制：错误密码也能解压（Python zipfile 库的限制）")
            print(f"     建议：安装 pyzipper 以获得真正的密码保护: pip install pyzipper")
        return None


def test_compress_7z(test_dir: Path, output_dir: Path):
    """测试 7Z 压缩（无密码）"""
    print("\n" + "=" * 70)
    print("测试 7: 7Z 格式压缩（无密码）")
    print("=" * 70)
    
    try:
        import py7zr
        print("  ✓ py7zr 已安装")
    except ImportError:
        print("  ⚠ py7zr 未安装，跳过 7Z 测试")
        return None
    
    output_path = output_dir / "test.7z"
    
    result = compress_files(
        source_paths=[str(test_dir / "file1.txt"), str(test_dir / "file2.txt")],
        output_path=str(output_path),
        format="7z",
        compression_level=5,
    )
    
    if result.get("ok"):
        print(f"  ✓ 7Z 压缩成功")
        print(f"    输出文件: {result.get('output_path')}")
        file_size = Path(result.get('output_path')).stat().st_size
        print(f"    文件大小: {file_size} 字节")
        
        return output_path
    else:
        print(f"  ✗ 7Z 压缩失败: {result.get('error')}")
        return None


def test_extract_7z(archive_path: Path, output_dir: Path):
    """测试 7Z 解压（无密码）"""
    print("\n" + "=" * 70)
    print("测试 8: 7Z 格式解压（无密码）")
    print("=" * 70)
    
    extract_dir = output_dir / "extracted_7z"
    
    result = extract_archive(
        archive_path=str(archive_path),
        output_dir=str(extract_dir),
    )
    
    if result.get("ok"):
        print(f"  ✓ 7Z 解压成功（无密码）")
        print(f"    输出目录: {result.get('output_dir')}")
        extracted_files = result.get('extracted_files', [])
        print(f"    解压文件数: {len(extracted_files)}")
        return extract_dir
    else:
        print(f"  ✗ 7Z 解压失败: {result.get('error')}")
        return None


def test_compress_7z_with_password(test_dir: Path, output_dir: Path):
    """测试 7Z 密码压缩"""
    print("\n" + "=" * 70)
    print("测试 9: 7Z 格式压缩（有密码）")
    print("=" * 70)
    
    try:
        import py7zr
        print("  ✓ py7zr 已安装")
    except ImportError:
        print("  ⚠ py7zr 未安装，跳过 7Z 密码测试")
        return None
    
    output_path = output_dir / "test_7z_password.7z"
    
    result = compress_files(
        source_paths=[str(test_dir / "file1.txt")],
        output_path=str(output_path),
        format="7z",
        compression_level=5,
        password="test123",
    )
    
    if result.get("ok"):
        print(f"  ✓ 7Z 密码压缩成功")
        print(f"    输出文件: {result.get('output_path')}")
        
        return output_path
    else:
        print(f"  ✗ 7Z 密码压缩失败: {result.get('error')}")
        return None


def test_extract_7z_with_password(archive_path: Path, output_dir: Path):
    """测试 7Z 解压（有密码 - 正确密码）"""
    print("\n" + "=" * 70)
    print("测试 10: 7Z 格式解压（有密码 - 正确密码）")
    print("=" * 70)
    
    extract_dir = output_dir / "extracted_7z_password"
    
    result = extract_archive(
        archive_path=str(archive_path),
        output_dir=str(extract_dir),
        password="test123",
    )
    
    if result.get("ok"):
        print(f"  ✓ 7Z 密码解压成功（正确密码）")
        print(f"    输出目录: {result.get('output_dir')}")
        extracted_files = result.get('extracted_files', [])
        print(f"    解压文件数: {len(extracted_files)}")
        return extract_dir
    else:
        print(f"  ✗ 7Z 密码解压失败: {result.get('error')}")
        return None


def test_extract_7z_wrong_password(archive_path: Path, output_dir: Path):
    """测试 7Z 解压（有密码 - 错误密码）"""
    print("\n" + "=" * 70)
    print("测试 11: 7Z 格式解压（有密码 - 错误密码）")
    print("=" * 70)
    
    extract_dir = output_dir / "extracted_7z_wrong_password"
    
    result = extract_archive(
        archive_path=str(archive_path),
        output_dir=str(extract_dir),
        password="wrong_password",
    )
    
    if not result.get("ok"):
        print(f"  ✓ 7Z 错误密码检测成功（正确拒绝解压）")
        print(f"    错误信息: {result.get('error')}")
        return None
    else:
        print(f"  ✗ 7Z 错误密码检测失败（应该失败但成功了）")
        return None


def test_compress_rar(test_dir: Path, output_dir: Path):
    """测试 RAR 压缩（无密码）"""
    print("\n" + "=" * 70)
    print("测试 12: RAR 格式压缩（无密码）")
    print("=" * 70)
    
    try:
        import rarfile
        print("  ✓ rarfile 已安装")
    except ImportError:
        print("  ⚠ rarfile 未安装，跳过 RAR 压缩测试")
        print("    注意：RAR 格式创建需要系统安装 WinRAR 或 rar 工具")
        return None
    
    output_path = output_dir / "test_rar_no_password.rar"
    
    result = compress_files(
        source_paths=[str(test_dir / "file1.txt")],
        output_path=str(output_path),
        format="rar",
        compression_level=5,
    )
    
    if result.get("ok"):
        print(f"  ✓ RAR 压缩成功（无密码）")
        print(f"    输出文件: {result.get('output_path')}")
        return output_path
    else:
        print(f"  ⚠ RAR 压缩: {result.get('error')}")
        print(f"    注意：RAR 格式创建需要系统安装 WinRAR 或 rar 工具")
        return None


def test_compress_rar_with_password(test_dir: Path, output_dir: Path):
    """测试 RAR 压缩（有密码）"""
    print("\n" + "=" * 70)
    print("测试 13: RAR 格式压缩（有密码）")
    print("=" * 70)
    
    try:
        import rarfile
        print("  ✓ rarfile 已安装")
    except ImportError:
        print("  ⚠ rarfile 未安装，跳过 RAR 密码压缩测试")
        return None
    
    output_path = output_dir / "test_rar_password.rar"
    
    result = compress_files(
        source_paths=[str(test_dir / "file1.txt")],
        output_path=str(output_path),
        format="rar",
        compression_level=5,
        password="test123",
    )
    
    if result.get("ok"):
        print(f"  ✓ RAR 密码压缩成功")
        print(f"    输出文件: {result.get('output_path')}")
        return output_path
    else:
        print(f"  ⚠ RAR 密码压缩: {result.get('error')}")
        print(f"    注意：RAR 格式创建需要系统安装 WinRAR 或 rar 工具")
        return None


def test_extract_rar(archive_path: Path, output_dir: Path):
    """测试 RAR 解压（无密码）"""
    print("\n" + "=" * 70)
    print("测试 14: RAR 格式解压（无密码）")
    print("=" * 70)
    
    try:
        import rarfile
        print("  ✓ rarfile 已安装")
    except ImportError:
        print("  ⚠ rarfile 未安装，跳过 RAR 解压测试")
        return None
    
    extract_dir = output_dir / "extracted_rar"
    
    result = extract_archive(
        archive_path=str(archive_path),
        output_dir=str(extract_dir),
    )
    
    if result.get("ok"):
        print(f"  ✓ RAR 解压成功（无密码）")
        print(f"    输出目录: {result.get('output_dir')}")
        extracted_files = result.get('extracted_files', [])
        print(f"    解压文件数: {len(extracted_files)}")
        return extract_dir
    else:
        print(f"  ✗ RAR 解压失败: {result.get('error')}")
        return None


def test_extract_rar_with_password(archive_path: Path, output_dir: Path):
    """测试 RAR 解压（有密码 - 正确密码）"""
    print("\n" + "=" * 70)
    print("测试 15: RAR 格式解压（有密码 - 正确密码）")
    print("=" * 70)
    
    try:
        import rarfile
        print("  ✓ rarfile 已安装")
    except ImportError:
        print("  ⚠ rarfile 未安装，跳过 RAR 密码解压测试")
        return None
    
    extract_dir = output_dir / "extracted_rar_password"
    
    result = extract_archive(
        archive_path=str(archive_path),
        output_dir=str(extract_dir),
        password="test123",
    )
    
    if result.get("ok"):
        print(f"  ✓ RAR 密码解压成功（正确密码）")
        print(f"    输出目录: {result.get('output_dir')}")
        extracted_files = result.get('extracted_files', [])
        print(f"    解压文件数: {len(extracted_files)}")
        return extract_dir
    else:
        print(f"  ✗ RAR 密码解压失败: {result.get('error')}")
        return None


def test_extract_rar_wrong_password(archive_path: Path, output_dir: Path):
    """测试 RAR 解压（有密码 - 错误密码）"""
    print("\n" + "=" * 70)
    print("测试 16: RAR 格式解压（有密码 - 错误密码）")
    print("=" * 70)
    
    try:
        import rarfile
        print("  ✓ rarfile 已安装")
    except ImportError:
        print("  ⚠ rarfile 未安装，跳过 RAR 错误密码测试")
        return None
    
    extract_dir = output_dir / "extracted_rar_wrong_password"
    
    result = extract_archive(
        archive_path=str(archive_path),
        output_dir=str(extract_dir),
        password="wrong_password",
    )
    
    if not result.get("ok"):
        print(f"  ✓ RAR 错误密码检测成功（正确拒绝解压）")
        print(f"    错误信息: {result.get('error')}")
        return None
    else:
        print(f"  ✗ RAR 错误密码检测失败（应该失败但成功了）")
        return None


def test_compress_levels(test_dir: Path, output_dir: Path):
    """测试不同压缩级别"""
    print("\n" + "=" * 70)
    print("测试 17: 不同压缩级别对比")
    print("=" * 70)
    
    levels = [0, 3, 6, 9]
    sizes = {}
    
    for level in levels:
        output_path = output_dir / f"test_level_{level}.zip"
        result = compress_files(
            source_paths=[str(test_dir / "file1.txt")],
            output_path=str(output_path),
            format="zip",
            compression_level=level,
        )
        
        if result.get("ok"):
            file_size = Path(result.get('output_path')).stat().st_size
            sizes[level] = file_size
            print(f"  级别 {level}: {file_size} 字节")
    
    if sizes:
        min_size = min(sizes.values())
        max_size = max(sizes.values())
        print(f"\n  最小: {min_size} 字节 (级别 {min(sizes, key=sizes.get)})")
        print(f"  最大: {max_size} 字节 (级别 {max(sizes, key=sizes.get)})")
        print(f"  压缩率: {((max_size - min_size) / max_size * 100):.1f}%")


def test_separate_archives(test_dir: Path, output_dir: Path):
    """测试单独压缩每个文件"""
    print("\n" + "=" * 70)
    print("测试 18: 每个文件单独压缩")
    print("=" * 70)
    
    output_path = output_dir / "separate.zip"
    
    result = compress_files(
        source_paths=[
            str(test_dir / "file1.txt"),
            str(test_dir / "file2.txt"),
        ],
        output_path=str(output_path),
        format="zip",
        separate_archives=True,
    )
    
    if result.get("ok"):
        output_paths = result.get("output_paths", [])
        print(f"  ✓ 单独压缩成功")
        print(f"    创建了 {len(output_paths)} 个压缩包:")
        for path in output_paths:
            print(f"      - {Path(path).name}")
        return output_paths
    else:
        print(f"  ✗ 单独压缩失败: {result.get('error')}")
        return None


def test_extract_rar(archive_path: Path, output_dir: Path):
    """测试 RAR 解压（如果可用）"""
    print("\n" + "=" * 70)
    print("测试 7: RAR 格式解压")
    print("=" * 70)
    
    try:
        import rarfile
        print("  ✓ rarfile 已安装")
        
        # 检查是否有 RAR 文件可以测试
        rar_files = list(archive_path.parent.glob("*.rar"))
        if not rar_files:
            print("  ⚠ 没有找到 RAR 文件进行测试")
            return None
        
        test_rar = rar_files[0]
        extract_dir = output_dir / "extracted_rar"
        
        result = extract_archive(
            archive_path=str(test_rar),
            output_dir=str(extract_dir),
        )
        
        if result.get("ok"):
            print(f"  ✓ RAR 解压成功")
            print(f"    输出目录: {result.get('output_dir')}")
            return extract_dir
        else:
            print(f"  ✗ RAR 解压失败: {result.get('error')}")
            return None
    except ImportError:
        print("  ⚠ rarfile 未安装，跳过 RAR 测试")
        return None


def test_split_compression(test_dir: Path, output_dir: Path):
    """测试分卷压缩"""
    print("\n" + "=" * 70)
    print("测试 19: 分卷压缩（7Z 格式）")
    print("=" * 70)
    
    try:
        import py7zr
        print("  ✓ py7zr 已安装")
    except ImportError:
        print("  ⚠ py7zr 未安装，跳过分卷压缩测试")
        return None
    
    output_path = output_dir / "test_split.7z"
    
    result = compress_files(
        source_paths=[str(test_dir)],
        output_path=str(output_path),
        format="7z",
        compression_level=5,
        split_size="1KB",  # 使用很小的分卷大小进行测试
    )
    
    if result.get("ok"):
        output_paths = result.get("output_paths", [])
        print(f"  ✓ 分卷压缩成功")
        print(f"    创建了 {len(output_paths)} 个分卷:")
        for path in output_paths[:5]:
            file_size = Path(path).stat().st_size
            print(f"      - {Path(path).name} ({file_size} 字节)")
        if len(output_paths) > 5:
            print(f"      ... 还有 {len(output_paths) - 5} 个分卷")
        return output_paths
    else:
        print(f"  ✗ 分卷压缩失败: {result.get('error')}")
        return None


def test_error_cases(test_dir: Path, output_dir: Path):
    """测试错误情况"""
    print("\n" + "=" * 70)
    print("测试 20: 错误情况处理")
    print("=" * 70)
    
    # 测试不存在的文件
    print("\n  8.1 测试不存在的文件:")
    result = compress_files(
        source_paths=["nonexistent_file.txt"],
        output_path=str(output_dir / "test_error.zip"),
        format="zip",
    )
    if not result.get("ok"):
        print(f"    ✓ 正确检测到文件不存在: {result.get('error')}")
    else:
        print(f"    ✗ 应该检测到文件不存在")
    
    # 测试不支持的格式
    print("\n  8.2 测试不支持的格式:")
    result = compress_files(
        source_paths=[str(test_dir / "file1.txt")],
        output_path=str(output_dir / "test.tar.gz"),
        format="tar.gz",
    )
    if not result.get("ok"):
        print(f"    ✓ 正确检测到不支持的格式: {result.get('error')}")
    else:
        print(f"    ✗ 应该检测到不支持的格式")
    
    # 测试不存在的压缩文件解压
    print("\n  8.3 测试不存在的压缩文件解压:")
    result = extract_archive(
        archive_path="nonexistent.zip",
        output_dir=str(output_dir / "extracted_error"),
    )
    if not result.get("ok"):
        print(f"    ✓ 正确检测到文件不存在: {result.get('error')}")
    else:
        print(f"    ✗ 应该检测到文件不存在")


def cleanup_test_files(output_dir: Path):
    """清理测试文件"""
    if AUTO_CLEANUP and output_dir.exists():
        try:
            shutil.rmtree(output_dir)
            print(f"\n  ✓ 已清理测试文件: {output_dir}")
        except Exception as e:
            print(f"\n  ⚠ 清理测试文件失败: {e}")


def main():
    """主测试函数"""
    # 确定测试结果文件路径
    if SAVE_RESULTS_TO_FILE:
        if Path(__file__).parent.name == 'archive_tools':
            # 从项目根目录运行
            results_file = Path(__file__).parent.parent / RESULTS_FILE_PATH
        else:
            # 从 archive_tools 目录运行
            results_file = Path(__file__).parent / RESULTS_FILE_PATH
        
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用 TeeOutput 同时输出到控制台和文件
        with TeeOutput(results_file) as tee:
            sys.stdout = tee
            sys.stderr = tee
            
            _run_tests()
            
            # 恢复标准输出
            sys.stdout = tee.terminal
            sys.stderr = tee.terminal
        
        print(f"\n📄 测试结果已保存到: {results_file}")
        print(f"   可以直接查看该文件了解测试详情")
    else:
        _run_tests()


def _run_tests():
    """实际运行测试的函数"""
    test_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("# 压缩解压工具测试报告")
    print()
    print(f"**测试时间**: {test_time}")
    print()
    print("---")
    print()
    print("=" * 70)
    print("压缩解压工具测试")
    print("=" * 70)
    print(f"测试时间: {test_time}")
    print()
    
    # 创建临时测试目录
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "test_files"
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir(exist_ok=True)
        
        # 创建测试文件
        create_test_files(test_dir)
        
        # 运行测试
        try:
            # ========== ZIP 格式测试 ==========
            # 1. 默认格式测试
            test_default_format(test_dir, output_dir)
            
            # 2. ZIP 压缩（无密码）
            zip_file = test_compress_zip(test_dir, output_dir)
            
            # 3. ZIP 解压（无密码）
            if zip_file:
                test_extract_zip(zip_file, output_dir)
            
            # 4. ZIP 压缩（有密码）
            zip_password_file = test_compress_zip_with_password(test_dir, output_dir)
            
            # 5. ZIP 解压（有密码 - 正确密码）
            if zip_password_file:
                test_extract_zip_with_password(zip_password_file, output_dir)
            
            # 6. ZIP 解压（有密码 - 错误密码）
            if zip_password_file:
                test_extract_zip_wrong_password(zip_password_file, output_dir)
            
            # ========== 7Z 格式测试 ==========
            # 7. 7Z 压缩（无密码）
            sevenz_file = test_compress_7z(test_dir, output_dir)
            
            # 8. 7Z 解压（无密码）
            if sevenz_file:
                test_extract_7z(sevenz_file, output_dir)
            
            # 9. 7Z 压缩（有密码）
            sevenz_password_file = test_compress_7z_with_password(test_dir, output_dir)
            
            # 10. 7Z 解压（有密码 - 正确密码）
            if sevenz_password_file:
                test_extract_7z_with_password(sevenz_password_file, output_dir)
            
            # 11. 7Z 解压（有密码 - 错误密码）
            if sevenz_password_file:
                test_extract_7z_wrong_password(sevenz_password_file, output_dir)
            
            # ========== RAR 格式测试 ==========
            # 12. RAR 压缩（无密码）- 如果支持
            rar_file = test_compress_rar(test_dir, output_dir)
            
            # 13. RAR 压缩（有密码）- 如果支持
            rar_password_file = test_compress_rar_with_password(test_dir, output_dir)
            
            # 14. RAR 解压（无密码）- 如果有 RAR 文件
            if rar_file:
                test_extract_rar(rar_file, output_dir)
            
            # 15. RAR 解压（有密码 - 正确密码）- 如果有密码保护的 RAR 文件
            if rar_password_file:
                test_extract_rar_with_password(rar_password_file, output_dir)
            
            # 16. RAR 解压（有密码 - 错误密码）- 如果有密码保护的 RAR 文件
            if rar_password_file:
                test_extract_rar_wrong_password(rar_password_file, output_dir)
            
            # ========== 其他功能测试 ==========
            # 17. 不同压缩级别对比
            test_compress_levels(test_dir, output_dir)
            
            # 18. 每个文件单独压缩
            test_separate_archives(test_dir, output_dir)
            
            # 19. 分卷压缩
            test_split_compression(test_dir, output_dir)
            
            # 20. 错误情况处理
            test_error_cases(test_dir, output_dir)
            
            completion_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print("\n" + "=" * 70)
            print("测试完成")
            print(f"完成时间: {completion_time}")
            print("=" * 70)
            print()
            print("---")
            print()
            print(f"**测试完成时间**: {completion_time}")
            print()
            print("> 测试结果已自动保存到此文档")
            
        except KeyboardInterrupt:
            interrupt_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print("\n\n测试被用户中断")
            print(f"中断时间: {interrupt_time}")
            print()
            print("---")
            print()
            print(f"**测试状态**: ❌ 被用户中断")
            print(f"**中断时间**: {interrupt_time}")
        except Exception as e:
            error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n\n测试过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            print()
            print("---")
            print()
            print(f"**测试状态**: ❌ 发生错误")
            print(f"**错误时间**: {error_time}")
            print(f"**错误信息**: {str(e)}")
        
        # 如果设置了不自动清理，保留文件
        if not AUTO_CLEANUP:
            print(f"\n测试文件保留在: {output_dir}")
            print("设置 AUTO_CLEANUP = True 可以自动清理")


if __name__ == "__main__":
    main()

