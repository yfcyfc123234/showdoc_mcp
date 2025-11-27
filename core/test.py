"""
ShowDoc 客户端测试脚本
统一测试文件，支持所有功能

使用方法：
1. 在 core 目录内运行：python test.py
2. 从项目根目录运行：python -m core.test
"""
import sys
import os
import json
from pathlib import Path

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

# 添加父目录到路径（如果在 core 目录内运行）
if Path(__file__).parent.name == 'core':
    sys.path.insert(0, str(Path(__file__).parent.parent))

from core import ShowDocClient, ShowDocNotFoundError, ShowDocAuthError


# ========== 配置参数（请修改为你的实际参数）==========
BASE_URL = "https://doc.cqfengli.com/web/#/item/password/76?page_id=0&redirect=%2F76"
COOKIE = None  # 可选，如果提供则使用 Cookie 认证
PASSWORD = "123456"  # 默认密码，如果未提供 COOKIE 则使用密码自动登录

# 节点名称（None 表示获取全部，或指定节点名称如 "订单"）
NODE_NAME = None

# 导出文件路径配置
# None: 使用默认文件名（showdoc_export_{item_id}.json）
# 字符串: 导出到指定路径，支持 {item_id} 占位符
# 例如: "output/showdoc_{item_id}.json" 或 "output/data.json"
EXPORT_PATH = None

# 自动导出控制
# True: 自动导出（如果 EXPORT_PATH 为 None，使用默认文件名）
# False: 交互式询问是否导出（仅在交互式环境下）
AUTO_EXPORT = True

# 是否显示详细的分类结构（True/False）
SHOW_DETAILS = True
# ====================================================


def print_tree(category, level=0, max_pages=3, max_children=2):
    """打印分类树结构"""
    indent = "  " * level
    print(f"{indent}[分类] {category.cat_name} (ID: {category.cat_id})")
    
    # 显示页面
    for page in category.pages[:max_pages]:
        if page.api_info:
            method = page.api_info.method
            url = page.api_info.url[:50] + "..." if len(page.api_info.url) > 50 else page.api_info.url
            print(f"{indent}  [页面] {page.page_title}")
            print(f"{indent}       -> {method} {url}")
        else:
            print(f"{indent}  [页面] {page.page_title}")
    
    if len(category.pages) > max_pages:
        print(f"{indent}  ... 还有 {len(category.pages) - max_pages} 个页面")
    
    # 递归显示子分类
    for child in category.children[:max_children]:
        print_tree(child, level + 1, max_pages, max_children)
    if len(category.children) > max_children:
        print(f"{indent}  ... 还有 {len(category.children) - max_children} 个子分类")


def count_pages(category):
    """递归统计页面数"""
    total = len(category.pages)
    api_count = sum(1 for p in category.pages if p.api_info)
    for child in category.children:
        child_total, child_api = count_pages(child)
        total += child_total
        api_count += child_api
    return total, api_count


def export_json(api_tree, export_path=None, auto_export=False):
    """导出 JSON 文件
    
    Args:
        api_tree: ApiTree 对象
        export_path: 导出路径，None 表示使用默认文件名
        auto_export: 是否自动导出，True 表示不询问直接导出
    
    Returns:
        导出文件的路径，如果未导出则返回 None
    """
    # 确定文件名
    if export_path is None:
        filename = f"showdoc_export_{api_tree.item_info.item_id}.json"
    else:
        filename = export_path
        # 替换占位符
        if "{item_id}" in filename:
            filename = filename.replace("{item_id}", api_tree.item_info.item_id)
    
    # 判断是否需要导出
    if not auto_export:
        # 交互式询问
        try:
            export = input("  是否导出为 JSON 文件？(y/n, 默认n): ").strip().lower()
            if export != 'y':
                print("  - 跳过导出")
                return None
        except EOFError:
            # 非交互式环境，如果不自动导出则跳过
            print("  - 跳过导出（非交互式环境，请设置 AUTO_EXPORT=True 启用自动导出）")
            return None
    
    # 确保目录存在
    export_dir = Path(filename).parent
    if export_dir and str(export_dir) != '.' and not export_dir.exists():
        export_dir.mkdir(parents=True, exist_ok=True)
    
    # 导出文件
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(api_tree.to_dict(), f, ensure_ascii=False, indent=2)
    
    return filename


def main():
    """主测试函数"""
    print("=" * 70)
    print("ShowDoc 客户端测试")
    print("=" * 70)
    print()
    
    try:
        # 步骤1: 初始化客户端
        print("[步骤 1] 初始化客户端...")
        try:
            client = ShowDocClient(BASE_URL, cookie=COOKIE, password=PASSWORD)
            print("[OK] 成功")
            print(f"  - 服务器地址: {client.server_base}")
            print(f"  - 项目 ID: {client.item_id}")
            print()
        except ShowDocAuthError as e:
            # 认证错误在初始化时发生，提供更详细的错误信息
            print("[失败]")
            raise  # 重新抛出，让下面的异常处理统一处理
        
        # 步骤2: 获取接口数据
        node_desc = NODE_NAME if NODE_NAME else "全部"
        print(f"[步骤 2] 获取接口数据 (节点: {node_desc})...")
        if not SHOW_DETAILS:
            print("  提示: 这可能需要一些时间，请稍候...")
        api_tree = client.get_all_apis(node_name=NODE_NAME)
        print("[OK] 成功获取数据")
        print()
        
        # 步骤3: 显示项目信息
        print("[步骤 3] 项目信息:")
        print(f"  - 项目 ID: {api_tree.item_info.item_id}")
        print(f"  - 项目名称: {api_tree.item_info.item_name}")
        print(f"  - 分类数量: {len(api_tree.categories)}")
        print()
        
        # 步骤4: 显示分类结构
        if SHOW_DETAILS:
            print("[步骤 4] 分类结构:")
            max_categories = 3 if len(api_tree.categories) > 3 else len(api_tree.categories)
            for i, category in enumerate(api_tree.categories[:max_categories], 1):
                print(f"\n分类 {i}:")
                print_tree(category, max_pages=3, max_children=2)
                if i < max_categories:
                    print()
            
            if len(api_tree.categories) > max_categories:
                print(f"\n... 还有 {len(api_tree.categories) - max_categories} 个分类")
            print()
        
        # 步骤5: 统计信息
        print("[步骤 5] 统计信息:")
        total_pages = 0
        total_api_pages = 0
        for cat in api_tree.categories:
            pages, api_pages = count_pages(cat)
            total_pages += pages
            total_api_pages += api_pages
        
        print(f"  - 总分类数: {len(api_tree.categories)}")
        print(f"  - 总页面数: {total_pages}")
        print(f"  - API 页面数: {total_api_pages}")
        print()
        
        # 步骤6: 导出 JSON
        print("[步骤 6] 导出数据")
        export_file = export_json(api_tree, EXPORT_PATH, AUTO_EXPORT)
        if export_file:
            print(f"  [OK] 已导出到: {export_file}")
        print()
        
        print("=" * 70)
        print("[OK] 测试完成！")
        print("=" * 70)
        
        return 0
        
    except ShowDocNotFoundError as e:
        print()
        print("=" * 70)
        print("❌ 错误: 未找到指定节点")
        print("=" * 70)
        print(f"\n错误详情: {e}")
        print("\n💡 解决方案:")
        print("  1. 检查节点名称是否正确（区分大小写）")
        print("  2. 使用 NODE_NAME = None 获取所有可用节点")
        print("  3. 查看上面的输出，确认正确的节点名称")
        return 1
    except ShowDocAuthError as e:
        print()
        print("=" * 70)
        print("❌ 错误: 认证失败")
        print("=" * 70)
        error_msg = str(e)
        print(f"\n错误详情: {error_msg}")
        
        # 根据错误信息提供更具体的建议
        if "密码错误" in error_msg:
            print("\n💡 解决方案:")
            print("  1. 检查 PASSWORD 配置是否正确")
            print("  2. 确认项目访问密码是否已更改")
        elif "验证码" in error_msg:
            print("\n💡 解决方案:")
            print("  1. 验证码识别失败，程序会自动重试")
            print("  2. 如果持续失败，可能是验证码图片质量问题")
            print("  3. 可以尝试使用 Cookie 认证（设置 COOKIE 参数）")
        elif "Cookie" in error_msg or "cookie" in error_msg:
            print("\n💡 解决方案:")
            print("  1. 检查 COOKIE 配置是否正确")
            print("  2. Cookie 可能已过期，请重新登录获取新 Cookie")
            print("  3. 获取 Cookie 方法：")
            print("     - 在浏览器中登录 ShowDoc")
            print("     - 打开开发者工具（F12）")
            print("     - Network 标签 → 任意请求 → Request Headers → Cookie")
        else:
            print("\n💡 解决方案:")
            print("  1. 检查 Cookie 或密码是否有效")
            print("  2. 尝试重新登录 ShowDoc 获取新的 Cookie")
            print("  3. 确认密码是否正确")
        return 1
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        return 1
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ 发生未预期的错误: {type(e).__name__}")
        print("=" * 70)
        print(f"\n错误类型: {type(e).__name__}")
        print(f"错误信息: {e}")
        print("\n详细堆栈:")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

