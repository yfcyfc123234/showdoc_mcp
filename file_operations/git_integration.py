"""
Git 集成工具

提供 Git 文件状态检查、自动添加等功能。
"""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

from .exceptions import FileOperationError, GitOperationError


def _run_git_command(cmd: List[str], cwd: Optional[Path] = None) -> tuple[str, str, int]:
    """运行 Git 命令"""
    try:
        result = subprocess.run(
            ["git"] + cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        raise GitOperationError("Git 未安装或不在 PATH 中")
    except subprocess.TimeoutExpired:
        raise GitOperationError("Git 命令执行超时")
    except Exception as e:
        raise GitOperationError(f"执行 Git 命令失败: {e}")


def _find_git_root(file_path: Path) -> Optional[Path]:
    """查找 Git 仓库根目录"""
    current = file_path.resolve()
    
    while current != current.parent:
        git_dir = current / ".git"
        if git_dir.exists():
            return current
        current = current.parent
    
    return None


def is_file_tracked(file_path: str | Path) -> bool:
    """
    检查文件是否在 Git 中跟踪
    
    Args:
        file_path: 文件路径
    
    Returns:
        是否被跟踪
    """
    path = Path(file_path).resolve()
    git_root = _find_git_root(path)
    
    if not git_root:
        return False
    
    relative_path = path.relative_to(git_root)
    stdout, stderr, returncode = _run_git_command(
        ["ls-files", "--error-unmatch", str(relative_path)],
        cwd=git_root,
    )
    
    return returncode == 0


def get_file_git_status(file_path: str | Path) -> Optional[str]:
    """
    获取文件的 Git 状态
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件状态（"untracked", "modified", "added", "deleted", "unchanged" 或 None）
    """
    path = Path(file_path).resolve()
    git_root = _find_git_root(path)
    
    if not git_root:
        return None
    
    relative_path = path.relative_to(git_root)
    
    # 检查是否被跟踪
    if not is_file_tracked(path):
        if path.exists():
            return "untracked"
        return None
    
    # 检查状态
    stdout, stderr, returncode = _run_git_command(
        ["status", "--porcelain", str(relative_path)],
        cwd=git_root,
    )
    
    if returncode != 0:
        return None
    
    status_line = stdout.strip()
    if not status_line:
        return "unchanged"
    
    # 解析状态
    status_code = status_line[:2]
    
    if status_code[0] == "M" or status_code[1] == "M":
        return "modified"
    elif status_code[0] == "A":
        return "added"
    elif status_code[0] == "D":
        return "deleted"
    elif status_code[0] == "?":
        return "untracked"
    else:
        return "unknown"


def is_file_ignored(file_path: str | Path) -> bool:
    """
    检查文件是否被 .gitignore 忽略
    
    Args:
        file_path: 文件路径
    
    Returns:
        是否被忽略
    """
    path = Path(file_path).resolve()
    git_root = _find_git_root(path)
    
    if not git_root:
        return False
    
    relative_path = path.relative_to(git_root)
    stdout, stderr, returncode = _run_git_command(
        ["check-ignore", "-q", str(relative_path)],
        cwd=git_root,
    )
    
    return returncode == 0


def add_file_to_git(
    file_path: str | Path,
    force: bool = False,
) -> bool:
    """
    添加文件到 Git
    
    Args:
        file_path: 文件路径
        force: 是否强制添加（即使被 .gitignore 忽略）
    
    Returns:
        是否成功
    """
    path = Path(file_path).resolve()
    git_root = _find_git_root(path)
    
    if not git_root:
        raise GitOperationError(f"文件不在 Git 仓库中: {path}")
    
    if not path.exists():
        raise FileOperationError(f"文件不存在: {path}")
    
    relative_path = path.relative_to(git_root)
    
    cmd = ["add"]
    if force:
        cmd.append("-f")
    cmd.append(str(relative_path))
    
    stdout, stderr, returncode = _run_git_command(cmd, cwd=git_root)
    
    if returncode != 0:
        raise GitOperationError(f"添加文件到 Git 失败: {stderr}")
    
    return True


def batch_add_to_git(
    file_paths: List[str | Path],
    force: bool = False,
) -> Dict[str, Any]:
    """
    批量添加文件到 Git
    
    Args:
        file_paths: 文件路径列表
        force: 是否强制添加
    
    Returns:
        操作结果字典
    """
    success_count = 0
    failed_count = 0
    failed_files = []
    
    for file_path in file_paths:
        try:
            add_file_to_git(file_path, force=force)
            success_count += 1
        except Exception as e:
            failed_count += 1
            failed_files.append({
                "file": str(file_path),
                "error": str(e),
            })
    
    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "failed_files": failed_files,
        "total_count": len(file_paths),
    }


def get_file_diff(file_path: str | Path) -> Optional[str]:
    """
    获取文件的 Git diff
    
    Args:
        file_path: 文件路径
    
    Returns:
        diff 内容，如果文件未修改则返回 None
    """
    path = Path(file_path).resolve()
    git_root = _find_git_root(path)
    
    if not git_root:
        return None
    
    relative_path = path.relative_to(git_root)
    
    stdout, stderr, returncode = _run_git_command(
        ["diff", str(relative_path)],
        cwd=git_root,
    )
    
    if returncode != 0 or not stdout.strip():
        return None
    
    return stdout

