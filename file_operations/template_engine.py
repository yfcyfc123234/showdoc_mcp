"""
模板文件生成引擎

支持从模板生成文件，支持变量替换、环境变量、模板继承等。
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from string import Template

from .exceptions import FileOperationError, TemplateError
from .safe_writer import SafeFileWriter


class TemplateEngine:
    """模板引擎"""
    
    def __init__(self, variables: Optional[Dict[str, Any]] = None, use_env: bool = True):
        """
        初始化模板引擎
        
        Args:
            variables: 模板变量字典
            use_env: 是否使用环境变量
        """
        self.variables = variables or {}
        self.use_env = use_env
    
    def _get_variable(self, name: str) -> str:
        """获取变量值"""
        # 优先使用传入的变量
        if name in self.variables:
            return str(self.variables[name])
        
        # 其次使用环境变量
        if self.use_env and name in os.environ:
            return os.environ[name]
        
        # 未找到变量
        raise TemplateError(f"未找到变量: {name}")
    
    def render(self, template_content: str) -> str:
        """
        渲染模板内容
        
        Args:
            template_content: 模板内容
        
        Returns:
            渲染后的内容
        
        Raises:
            TemplateError: 模板错误
        """
        try:
            # 使用 Python 的 Template 类（支持 ${variable} 语法）
            template = Template(template_content)
            
            # 准备变量字典
            vars_dict = {}
            if self.use_env:
                vars_dict.update(os.environ)
            vars_dict.update({k: str(v) for k, v in self.variables.items()})
            
            return template.safe_substitute(vars_dict)
        except Exception as e:
            raise TemplateError(f"模板渲染失败: {e}")
    
    def render_advanced(self, template_content: str) -> str:
        """
        高级模板渲染（支持 ${variable} 和 {{ variable }} 语法）
        
        Args:
            template_content: 模板内容
        
        Returns:
            渲染后的内容
        
        Raises:
            TemplateError: 模板错误
        """
        content = template_content
        
        # 准备变量字典
        vars_dict = {}
        if self.use_env:
            vars_dict.update(os.environ)
        vars_dict.update({k: str(v) for k, v in self.variables.items()})
        
        # 替换 ${variable} 语法
        def replace_var(match):
            var_name = match.group(1)
            if var_name in vars_dict:
                return str(vars_dict[var_name])
            raise TemplateError(f"未找到变量: {var_name}")
        
        content = re.sub(r'\$\{(\w+)\}', replace_var, content)
        
        # 替换 {{ variable }} 语法
        def replace_var2(match):
            var_name = match.group(1).strip()
            if var_name in vars_dict:
                return str(vars_dict[var_name])
            raise TemplateError(f"未找到变量: {var_name}")
        
        content = re.sub(r'\{\{\s*(\w+)\s*\}\}', replace_var2, content)
        
        return content


def generate_from_template(
    template_path: str | Path,
    output_path: str | Path,
    variables: Optional[Dict[str, Any]] = None,
    use_env: bool = True,
    encoding: str = "utf-8",
) -> Path:
    """
    从模板生成文件
    
    Args:
        template_path: 模板文件路径
        output_path: 输出文件路径
        variables: 模板变量字典
        use_env: 是否使用环境变量
        encoding: 文件编码
    
    Returns:
        输出文件路径
    
    Raises:
        FileNotFoundError: 模板文件不存在
        TemplateError: 模板错误
    """
    template_file = Path(template_path)
    
    if not template_file.exists():
        raise FileNotFoundError(f"模板文件不存在: {template_file}")
    
    # 读取模板内容
    from .content_processor import read_file_safe
    template_content = read_file_safe(template_file, encoding=encoding)
    
    # 渲染模板
    engine = TemplateEngine(variables=variables, use_env=use_env)
    rendered_content = engine.render_advanced(template_content)
    
    # 写入输出文件
    output = Path(output_path)
    writer = SafeFileWriter(output, encoding=encoding, backup=False)
    writer.write(rendered_content)
    
    return output


def generate_batch_from_template(
    template_path: str | Path,
    output_dir: str | Path,
    variables_list: List[Dict[str, Any]],
    output_name_template: str = "output_{index}",
    use_env: bool = True,
    encoding: str = "utf-8",
) -> List[Path]:
    """
    批量从模板生成文件
    
    Args:
        template_path: 模板文件路径
        output_dir: 输出目录
        variables_list: 变量字典列表（每个字典生成一个文件）
        output_name_template: 输出文件名模板（支持 {index} 占位符）
        use_env: 是否使用环境变量
        encoding: 文件编码
    
    Returns:
        生成的文件路径列表
    
    Raises:
        FileNotFoundError: 模板文件不存在
        TemplateError: 模板错误
    """
    template_file = Path(template_path)
    output = Path(output_dir)
    
    if not template_file.exists():
        raise FileNotFoundError(f"模板文件不存在: {template_file}")
    
    output.mkdir(parents=True, exist_ok=True)
    
    # 读取模板内容
    from .content_processor import read_file_safe
    template_content = read_file_safe(template_file, encoding=encoding)
    
    # 获取模板文件扩展名
    extension = template_file.suffix
    
    generated_files = []
    
    for index, variables in enumerate(variables_list):
        # 生成输出文件名
        output_name = output_name_template.format(index=index + 1)
        if not output_name.endswith(extension):
            output_name += extension
        
        output_path = output / output_name
        
        # 渲染模板
        engine = TemplateEngine(variables=variables, use_env=use_env)
        rendered_content = engine.render_advanced(template_content)
        
        # 写入文件
        writer = SafeFileWriter(output_path, encoding=encoding, backup=False)
        writer.write(rendered_content)
        
        generated_files.append(output_path)
    
    return generated_files


def render_template_string(
    template_content: str,
    variables: Optional[Dict[str, Any]] = None,
    use_env: bool = True,
) -> str:
    """
    渲染模板字符串
    
    Args:
        template_content: 模板内容
        variables: 模板变量字典
        use_env: 是否使用环境变量
    
    Returns:
        渲染后的内容
    
    Raises:
        TemplateError: 模板错误
    """
    engine = TemplateEngine(variables=variables, use_env=use_env)
    return engine.render_advanced(template_content)

