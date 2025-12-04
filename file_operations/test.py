"""
File Operations 模块测试脚本
"""

import tempfile
from pathlib import Path

from file_operations import (
    create_file,
    read_file_safe,
    write_file_safe,
    copy_file,
    delete_file,
    find_files,
    search_content,
    generate_from_template,
    get_file_info,
)


def test_basic_operations():
    """测试基础文件操作"""
    print("测试基础文件操作...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        
        # 创建文件
        create_file(test_file, "Hello, World!")
        assert test_file.exists()
        
        # 读取文件
        content = read_file_safe(test_file)
        assert content == "Hello, World!"
        
        # 写入文件
        write_file_safe(test_file, "Updated content")
        content = read_file_safe(test_file)
        assert content == "Updated content"
        
        # 复制文件
        copy_file(test_file, Path(tmpdir) / "test_copy.txt")
        assert (Path(tmpdir) / "test_copy.txt").exists()
        
        # 获取文件信息
        info = get_file_info(test_file)
        assert info["size"] > 0
        
        print("✓ 基础文件操作测试通过")


def test_file_search():
    """测试文件搜索"""
    print("测试文件搜索...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试文件
        (Path(tmpdir) / "test1.py").write_text("import os")
        (Path(tmpdir) / "test2.py").write_text("import sys")
        (Path(tmpdir) / "test3.txt").write_text("some text")
        
        # 查找 Python 文件
        files = find_files(tmpdir, extension=".py")
        assert len(files) == 2
        
        # 搜索内容
        results = search_content(tmpdir, "import os", pattern="*.py")
        assert len(results) == 1
        assert "test1.py" in results[0]["file"]
        
        print("✓ 文件搜索测试通过")


def test_template_engine():
    """测试模板引擎"""
    print("测试模板引擎...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        template_file = Path(tmpdir) / "template.txt"
        output_file = Path(tmpdir) / "output.txt"
        
        # 创建模板
        template_file.write_text("Hello, ${name}!")
        
        # 生成文件
        generate_from_template(
            template_file,
            output_file,
            variables={"name": "World"},
        )
        
        content = read_file_safe(output_file)
        assert "Hello, World!" in content
        
        print("✓ 模板引擎测试通过")


def main():
    """运行所有测试"""
    print("=" * 50)
    print("File Operations 模块测试")
    print("=" * 50)
    
    try:
        test_basic_operations()
        test_file_search()
        test_template_engine()
        
        print("=" * 50)
        print("所有测试通过！")
        print("=" * 50)
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

