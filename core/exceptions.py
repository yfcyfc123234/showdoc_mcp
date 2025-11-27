"""
ShowDoc 自定义异常类
"""


class ShowDocError(Exception):
    """ShowDoc 基础异常类"""
    pass


class ShowDocAuthError(ShowDocError):
    """认证错误：Cookie 无效或过期"""
    pass


class ShowDocCaptchaError(ShowDocError):
    """验证码处理失败"""
    pass


class ShowDocNotFoundError(ShowDocError):
    """资源未找到：节点、页面不存在等"""
    pass


class ShowDocParseError(ShowDocError):
    """数据解析错误：URL 解析、JSON 解析等"""
    pass


class ShowDocNetworkError(ShowDocError):
    """网络请求错误：连接失败、超时等"""
    pass

