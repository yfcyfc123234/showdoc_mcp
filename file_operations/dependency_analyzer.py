"""
依赖关系分析工具

提供导入语句解析、文件引用查找、依赖图构建等功能。
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Set, Optional, Tuple
from collections import defaultdict

# 使用内置异常
from .content_processor import read_file_safe
from .file_search import find_files


# 不同语言的导入模式
IMPORT_PATTERNS = {
    "python": [
        re.compile(r'^import\s+(\S+)'),
        re.compile(r'^from\s+(\S+)\s+import'),
    ],
    "javascript": [
        re.compile(r'^import\s+.*?from\s+["\']([^"\']+)["\']'),
        re.compile(r'^const\s+.*?=\s+require\(["\']([^"\']+)["\']'),
    ],
    "dart": [
        re.compile(r'^import\s+["\']([^"\']+)["\']'),
    ],
    "kotlin": [
        re.compile(r'^import\s+([\w.]+)'),
    ],
    "java": [
        re.compile(r'^import\s+([\w.]+)'),
    ],
}


def detect_language(file_path: Path) -> Optional[str]:
    """检测文件语言"""
    ext = file_path.suffix.lower()
    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "javascript",
        ".tsx": "javascript",
        ".dart": "dart",
        ".kt": "kotlin",
        ".java": "java",
    }
    return language_map.get(ext)


def parse_imports(
    file_path: str | Path,
    language: Optional[str] = None,
) -> List[str]:
    """
    解析文件中的导入语句
    
    Args:
        file_path: 文件路径
        language: 语言类型（如果为 None 则自动检测）
    
    Returns:
        导入的模块/包名列表
    
    Raises:
        FileNotFoundError: 文件不存在
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    if language is None:
        language = detect_language(path)
    
    if language is None or language not in IMPORT_PATTERNS:
        return []
    
    content = read_file_safe(path)
    lines = content.splitlines()
    
    imports = []
    patterns = IMPORT_PATTERNS[language]
    
    for line in lines:
        for pattern in patterns:
            match = pattern.match(line.strip())
            if match:
                import_name = match.group(1)
                imports.append(import_name)
                break
    
    return imports


def find_file_references(
    target_file: str | Path,
    search_dir: str | Path,
    language: Optional[str] = None,
) -> List[Path]:
    """
    查找哪些文件引用了目标文件
    
    Args:
        target_file: 目标文件路径
        search_dir: 搜索目录
        language: 语言类型（如果为 None 则自动检测）
    
    Returns:
        引用目标文件的文件路径列表
    """
    target = Path(target_file)
    search = Path(search_dir)
    
    if not target.exists():
        raise FileNotFoundError(f"目标文件不存在: {target}")
    
    if language is None:
        language = detect_language(target)
    
    if language is None:
        return []
    
    # 获取目标文件的模块名（简化处理）
    target_stem = target.stem
    target_parent = target.parent
    
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
        extensions = []
    
    reference_files = []
    
    for ext in extensions:
        files = find_files(search, extension=ext, recursive=True)
        for file_path in files:
            if file_path == target:
                continue
            
            imports = parse_imports(file_path, language=language)
            
            # 检查是否引用了目标文件
            for imp in imports:
                # 简单的匹配逻辑（实际应该更复杂）
                if target_stem in imp or str(target.relative_to(search.parent)) in imp:
                    reference_files.append(file_path)
                    break
    
    return reference_files


def find_unused_files(
    directory: str | Path,
    language: Optional[str] = None,
) -> List[Path]:
    """
    查找未使用的文件
    
    Args:
        directory: 目录路径
        language: 语言类型（如果为 None 则自动检测）
    
    Returns:
        未使用的文件路径列表
    """
    dir_path = Path(directory)
    
    if language is None:
        # 尝试从目录中的文件检测语言
        files = list(dir_path.rglob("*"))
        for f in files:
            if f.is_file():
                lang = detect_language(f)
                if lang:
                    language = lang
                    break
    
    if language is None:
        return []
    
    # 获取所有文件
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
    
    all_files = []
    for ext in extensions:
        all_files.extend(find_files(dir_path, extension=ext, recursive=True))
    
    # 构建引用关系
    referenced_files = set()
    for file_path in all_files:
        refs = find_file_references(file_path, dir_path, language)
        referenced_files.update(refs)
    
    # 找出未引用的文件（排除入口文件，如 main.py, index.js 等）
    entry_files = {"main", "index", "__init__", "app"}
    unused = []
    
    for file_path in all_files:
        if file_path in referenced_files:
            continue
        if file_path.stem.lower() in entry_files:
            continue
        unused.append(file_path)
    
    return unused


def build_dependency_graph(
    directory: str | Path,
    language: Optional[str] = None,
) -> Dict[str, Any]:
    """
    构建依赖关系图
    
    Args:
        directory: 目录路径
        language: 语言类型（如果为 None 则自动检测）
    
    Returns:
        依赖图字典，包含：
        - nodes: 节点列表（文件路径）
        - edges: 边列表（依赖关系）
        - graph: 邻接表表示
    """
    dir_path = Path(directory)
    
    if language is None:
        files = list(dir_path.rglob("*"))
        for f in files:
            if f.is_file():
                lang = detect_language(f)
                if lang:
                    language = lang
                    break
    
    if language is None:
        return {"nodes": [], "edges": [], "graph": {}}
    
    # 获取所有文件
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
        return {"nodes": [], "edges": [], "graph": {}}
    
    all_files = []
    for ext in extensions:
        all_files.extend(find_files(dir_path, extension=ext, recursive=True))
    
    # 构建文件到索引的映射
    file_to_index = {f: i for i, f in enumerate(all_files)}
    graph = defaultdict(set)
    edges = []
    
    # 分析每个文件的依赖
    for file_path in all_files:
        imports = parse_imports(file_path, language)
        file_idx = file_to_index[file_path]
        
        for imp in imports:
            # 尝试找到被导入的文件（简化实现）
            for other_file in all_files:
                if other_file == file_path:
                    continue
                if other_file.stem in imp or str(other_file.relative_to(dir_path)) in imp:
                    other_idx = file_to_index[other_file]
                    graph[file_idx].add(other_idx)
                    edges.append({
                        "from": str(file_path.relative_to(dir_path)),
                        "to": str(other_file.relative_to(dir_path)),
                    })
                    break
    
    return {
        "nodes": [str(f.relative_to(dir_path)) for f in all_files],
        "edges": edges,
        "graph": {str(k): list(v) for k, v in graph.items()},
    }

