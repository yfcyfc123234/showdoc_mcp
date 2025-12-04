"""
文件操作异常定义
"""


class FileOperationError(Exception):
    """文件操作基础异常类"""
    pass


# 使用内置异常，不重新定义
# FileNotFoundError 和 PermissionError 是 Python 内置异常
# 如果需要自定义行为，可以继承它们


class EncodingError(FileOperationError):
    """编码错误异常"""
    pass


class TemplateError(FileOperationError):
    """模板错误异常"""
    pass


class InvalidPathError(FileOperationError):
    """无效路径异常"""
    pass


class OperationCancelledError(FileOperationError):
    """操作被取消异常"""
    pass


class BackupError(FileOperationError):
    """备份错误异常"""
    pass


class GitOperationError(FileOperationError):
    """Git 操作错误异常"""
    pass

