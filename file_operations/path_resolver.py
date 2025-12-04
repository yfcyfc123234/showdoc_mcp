"""
路径和引用处理工具

提供导入路径解析、文件引用查找、路径更新等功能。
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from .exceptions import FileOperationError
from .content_processor import read_file_safe, replace_content
from .file_search import find_files


def normalize_path(path: str | Path) -> Path:
    """
    规范化路径
    
    Args:
        path: 路径字符串或 Path 对象
    
    Returns:
        规范化的 Path 对象
    """
    return Path(path).resolve()


def resolve_import_path(
    import_statement: str,
    current_file: str | Path,
    project_root: Optional[str | Path] = None,
) -> Optional[Path]:
    """
    解析导入路径为实际文件路径
    
    Args:
        import_statement: 导入语句（如 "from module import class" 或 "import module"）
        current_file: 当前文件路径
        project_root: 项目根目录（如果为 None 则从 current_file 推断）
    
    Returns:
        解析后的文件路径，如果无法解析则返回 None
    """
    current = Path(current_file).resolve()
    
    if project_root:
        root = Path(project_root).resolve()
    else:
        # 尝试从当前文件推断项目根目录
        root = current.parent
        # 向上查找包含常见项目标识的目录
        for parent in current.parents:
            if (parent / "pyproject.toml").exists() or \
               (parent / "package.json").exists() or \
               (parent / "pubspec.yaml").exists() or \
               (parent / "build.gradle").exists():
                root = parent
                break
    
    # 解析导入语句
    # Python: "from package.module import class" 或 "import module"
    # JavaScript: "import module from './module'" 或 "const module = require('./module')"
    # Dart: "import 'package:app/module.dart'"
    # Kotlin: "import com.example.module"
    
    # 简化实现：提取模块名
    module_match = re.search(r'from\s+["\']?([^"\']+)["\']?|import\s+["\']?([^"\']+)["\']?', import_statement)
    if not module_match:
        return None
    
    module_name = module_match.group(1) or module_match.group(2)
    if not module_name:
        return None
    
    # 尝试不同的路径解析策略
    # 1. 相对路径（以 . 或 .. 开头）
    if module_name.startswith(".") or module_name.startswith("/"):
        if module_name.startswith("."):
            # 相对导入
            parts = module_name.split(".")
            base_path = current.parent
            for part in parts:
                if part == "":
                    continue
                elif part == "..":
                    base_path = base_path.parent
                else:
                    base_path = base_path / part
            
            # 尝试不同的扩展名
            for ext in [".py", ".js", ".ts", ".dart", ".kt", ".java"]:
                file_path = base_path.with_suffix(ext)
                if file_path.exists():
                    return file_path
                
                # 尝试作为目录的 __init__.py 或 index.js
                if ext == ".py":
                    init_file = base_path / "__init__.py"
                    if init_file.exists():
                        return init_file
                elif ext in [".js", ".ts"]:
                    index_file = base_path / f"index{ext}"
                    if index_file.exists():
                        return index_file
        else:
            # 绝对路径
            file_path = root / module_name.lstrip("/")
            if file_path.exists():
                return file_path
    
    # 2. 包导入（如 package.module）
    else:
        # 将点分隔的模块名转换为路径
        parts = module_name.split(".")
        base_path = root
        
        for part in parts:
            base_path = base_path / part
        
        # 尝试不同的扩展名
        for ext in [".py", ".js", ".ts", ".dart", ".kt", ".java"]:
            file_path = base_path.with_suffix(ext)
            if file_path.exists():
                return file_path
            
            # 尝试作为目录
            if ext == ".py":
                init_file = base_path / "__init__.py"
                if init_file.exists():
                    return init_file
            elif ext in [".js", ".ts"]:
                index_file = base_path / f"index{ext}"
                if index_file.exists():
                    return index_file
    
    return None


def find_file_references_by_path(
    target_file: str | Path,
    search_dir: str | Path,
    language: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    查找文件引用（通过路径）
    
    Args:
        target_file: 目标文件路径
        search_dir: 搜索目录
        language: 语言类型（如果为 None 则自动检测）
    
    Returns:
        引用信息列表，每个引用包含：
        - file: 引用文件路径
        - line_number: 行号
        - import_statement: 导入语句
    """
    from .dependency_analyzer import detect_language, parse_imports
    
    target = Path(target_file).resolve()
    search = Path(search_dir).resolve()
    
    if not target.exists():
        raise FileNotFoundError(f"目标文件不存在: {target}")
    
    if language is None:
        language = detect_language(target)
    
    if language is None:
        return []
    
    # 获取目标文件的相对路径（相对于搜索目录）
    try:
        target_relative = target.relative_to(search)
    except ValueError:
        # 目标文件不在搜索目录内
        return []
    
    # 查找所有可能的引用文件
    if language == "python":
        extensions = [".py"]
    elif language == "javascript":
        extensions = [".js", ".jsx", ".ts", ".tsx"]
    elif language == "dart":
        extensions = [".dart"]
    elif language == "kotlin":
        extensions = [".kt"]
    elif language == "java":
        extensions = [".java"]
    else:
        return []
    
    references = []
    
    for ext in extensions:
        files = find_files(search, extension=ext, recursive=True)
        for file_path in files:
            if file_path == target:
                continue
            
            content = read_file_safe(file_path)
            lines = content.splitlines()
            
            # 检查每一行的导入语句
            for line_num, line in enumerate(lines, 1):
                imports = parse_imports_from_line(line, language)
                for imp in imports:
                    resolved = resolve_import_path(imp, file_path, search)
                    if resolved and resolved.resolve() == target.resolve():
                        references.append({
                            "file": str(file_path),
                            "line_number": line_num,
                            "import_statement": imp,
                        })
    
    return references


def parse_imports_from_line(line: str, language: str) -> List[str]:
    """从单行解析导入语句"""
    imports = []
    
    if language == "python":
        if re.match(r'^\s*(import|from)\s+', line):
            imports.append(line.strip())
    elif language == "javascript":
        if re.match(r'^\s*import\s+', line) or re.search(r'require\(["\']', line):
            imports.append(line.strip())
    elif language == "dart":
        if re.match(r'^\s*import\s+', line):
            imports.append(line.strip())
    elif language in ["kotlin", "java"]:
        if re.match(r'^\s*import\s+', line):
            imports.append(line.strip())
    
    return imports


def update_import_paths(
    file_path: str | Path,
    old_path: str | Path,
    new_path: str | Path,
    project_root: Optional[str | Path] = None,
) -> int:
    """
    更新文件中的导入路径
    
    Args:
        file_path: 要更新的文件路径
        old_path: 旧路径
        new_path: 新路径
        project_root: 项目根目录
    
    Returns:
        更新的导入语句数量
    """
    from .dependency_analyzer import detect_language
    
    path = Path(file_path)
    old = Path(old_path).resolve()
    new = Path(new_path).resolve()
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    language = detect_language(path)
    if language is None:
        return 0
    
    content = read_file_safe(path)
    lines = content.splitlines(keepends=True)
    
    updated_count = 0
    
    for i, line in enumerate(lines):
        imports = parse_imports_from_line(line, language)
        for imp in imports:
            resolved = resolve_import_path(imp, path, project_root)
            if resolved and resolved.resolve() == old.resolve():
                # 计算新的相对路径
                new_relative = new.relative_to(path.parent)
                # 更新导入语句（简化实现）
                # 实际应该更智能地处理不同语言的导入语法
                new_import = _generate_new_import(imp, new_relative, language)
                lines[i] = line.replace(imp, new_import)
                updated_count += 1
    
    if updated_count > 0:
        new_content = "".join(lines)
        from .safe_writer import SafeFileWriter
        writer = SafeFileWriter(path, backup=True)
        writer.write(new_content)
    
    return updated_count


def _generate_new_import(old_import: str, new_relative: Path, language: str) -> str:
    """生成新的导入语句"""
    # 简化实现，实际应该更智能
    if language == "python":
        # 将路径转换为点分隔的模块名
        parts = new_relative.parts
        module_name = ".".join(parts).replace(".py", "").replace("/", ".")
        if old_import.startswith("from"):
            return f"from {module_name} import"
        else:
            return f"import {module_name}"
    else:
        # 其他语言类似处理
        return old_import

