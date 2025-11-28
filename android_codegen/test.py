"""
Android 代码生成器测试脚本
统一测试文件，支持所有功能

使用方法：
1. 在 android_codegen 目录内运行：python test.py
2. 从项目根目录运行：python -m android_codegen.test
"""
import sys
import os
import shutil
import json
from pathlib import Path

# 设置控制台编码为 UTF-8（Windows）
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass
    if hasattr(sys.stderr, 'reconfigure'):
        try:
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass

# 添加父目录到路径（如果在 android_codegen 目录内运行）
if Path(__file__).parent.name == 'android_codegen':
    sys.path.insert(0, str(Path(__file__).parent.parent))

from core import ShowDocClient, ShowDocNotFoundError, ShowDocAuthError
from android_codegen import AndroidCodeGenerator


# ========== 配置参数（请修改为你的实际参数）==========
BASE_URL = "https://www.showdoc.com.cn/2598847052437483/0"
COOKIE = None  # 可选，如果提供则使用 Cookie 认证
PASSWORD = "123456"  # 默认密码，如果未提供 COOKIE 则使用密码自动登录

# 节点名称（None 表示获取全部，或指定节点名称如 "订单"）
NODE_NAME = None

# Android 代码生成配置
BASE_PACKAGE = "com.example.api"  # Android 包名
OUTPUT_DIR = "output/android_output"     # 输出目录（默认统一到 output 文件夹）

# 输出目录配置
# None: 使用默认目录（android_output）
# 字符串: 导出到指定目录，支持 {item_id} 占位符
# 例如: "output/android_{item_id}" 或 "output/android_code"
OUTPUT_DIR_CONFIG = None

# 自动生成控制
# True: 自动生成代码（如果 OUTPUT_DIR_CONFIG 为 None，使用默认目录）
# False: 交互式询问是否生成（仅在交互式环境下）
AUTO_GENERATE = True

# 是否显示详细的 API 信息（True/False）
SHOW_DETAILS = True
# ====================================================


def count_apis(category):
    """递归统计 API 数量"""
    api_count = sum(1 for p in category.pages if p.api_info)
    for child in category.children:
        api_count += count_apis(child)
    return api_count


def count_pages(category):
    """递归统计页面数"""
    total = len(category.pages)
    api_count = sum(1 for p in category.pages if p.api_info)
    for child in category.children:
        child_total, child_api = count_pages(child)
        total += child_total
        api_count += child_api
    return total, api_count


def print_api_summary(api_tree):
    """打印 API 摘要信息"""
    print("[API 摘要信息]")
    
    total_pages = 0
    total_api_pages = 0
    
    def collect_apis(category, apis_list):
        for page in category.pages:
            if page.api_info:
                apis_list.append({
                    "title": page.page_title,
                    "method": page.api_info.method,
                    "url": page.api_info.url,
                    "category": category.cat_name
                })
        for child in category.children:
            collect_apis(child, apis_list)
    
    all_apis = []
    for category in api_tree.categories:
        pages, api_pages = count_pages(category)
        total_pages += pages
        total_api_pages += api_pages
        collect_apis(category, all_apis)
    
    print(f"  - 总 API 数量: {total_api_pages}")
    
    if SHOW_DETAILS and all_apis:
        print("\n  [API 列表]")
        max_show = 5
        for i, api in enumerate(all_apis[:max_show], 1):
            url_short = api["url"][:50] + "..." if len(api["url"]) > 50 else api["url"]
            print(f"    {i}. [{api['method']}] {api['title']}")
            print(f"       分类: {api['category']}")
            print(f"       URL: {url_short}")
        
        if len(all_apis) > max_show:
            print(f"    ... 还有 {len(all_apis) - max_show} 个 API")
    
    print()


def get_output_dir(api_tree, output_dir_config=None, auto_generate=False):
    """确定输出目录
    
    Args:
        api_tree: ApiTree 对象
        output_dir_config: 输出目录配置，None 表示使用默认目录
        auto_generate: 是否自动生成，True 表示不询问直接生成
    
    Returns:
        输出目录路径，如果未生成则返回 None
    """
    # 确定输出目录
    if output_dir_config is None:
        output_dir = OUTPUT_DIR
    else:
        output_dir = output_dir_config
        # 替换占位符
        if "{item_id}" in output_dir:
            output_dir = output_dir.replace("{item_id}", api_tree.item_info.item_id)
    
    # 判断是否需要生成
    if not auto_generate:
        # 交互式询问
        try:
            generate = input(f"  是否生成 Android 代码到 '{output_dir}' ？(y/n, 默认n): ").strip().lower()
            if generate != 'y':
                print("  - 跳过生成")
                return None
        except EOFError:
            # 非交互式环境，如果不自动生成则跳过
            print("  - 跳过生成（非交互式环境，请设置 AUTO_GENERATE=True 启用自动生成）")
            return None
    
    return output_dir


def main():
    """主测试函数"""
    print("=" * 70)
    print("Android 代码生成器测试")
    print("=" * 70)
    print()
    
    try:
        # 步骤1: 初始化客户端
        print("[步骤 1] 初始化 ShowDoc 客户端...")
        client = ShowDocClient(BASE_URL, cookie=COOKIE, password=PASSWORD)
        print("[OK] 成功")
        print(f"  - 服务器地址: {client.server_base}")
        print(f"  - 项目 ID: {client.item_id}")
        print()
        
        # 步骤2: 获取接口数据
        node_desc = NODE_NAME if NODE_NAME else "全部"
        print(f"[步骤 2] 获取接口数据 (节点: {node_desc})...")
        if not SHOW_DETAILS:
            print("  提示: 这可能需要一些时间，请稍候...")
        api_tree = client.get_all_apis(node_name=NODE_NAME)
        print("[OK] 成功获取数据")
        
        # 自动保存接口数据快照
        try:
            from datetime import datetime
            snapshot_dir = Path("output/showdoc_snapshots")
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c for c in api_tree.item_info.item_name if c.isalnum() or c in (" ", "-", "_")).strip()[:30]
            if safe_name:
                snapshot_file = snapshot_dir / f"{api_tree.item_info.item_id}_{safe_name}_{timestamp}.json"
            else:
                snapshot_file = snapshot_dir / f"{api_tree.item_info.item_id}_{timestamp}.json"
            snapshot_file.write_text(
                json.dumps(api_tree.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"  - 接口数据已保存: {snapshot_file}")
        except Exception as e:
            print(f"  - 警告: 保存接口数据快照失败: {e}")
        
        print()
        
        # 步骤3: 显示项目信息
        print("[步骤 3] 项目信息:")
        print(f"  - 项目 ID: {api_tree.item_info.item_id}")
        print(f"  - 项目名称: {api_tree.item_info.item_name}")
        print(f"  - 分类数量: {len(api_tree.categories)}")
        print()
        
        # 步骤4: 显示 API 摘要
        print_api_summary(api_tree)
        
        # 步骤5: 确定输出目录
        print("[步骤 4] 配置生成参数")
        output_dir = get_output_dir(api_tree, OUTPUT_DIR_CONFIG, AUTO_GENERATE)
        if not output_dir:
            print()
            print("=" * 70)
            print("[INFO] 测试结束（未生成代码）")
            print("=" * 70)
            return 0
        
        print(f"  - 基础包名: {BASE_PACKAGE}")
        print(f"  - 输出目录: {output_dir}")
        print()
        
        # 步骤5: 生成 Android 代码（使用版本控制，不再删除旧目录）
        print("[步骤 5] 生成 Android 代码...")
        print("  提示: 正在生成 Retrofit Service、实体类和配置文件...")
        print("  提示: 已启用版本控制，将只更新有变化的文件")
        
        generator = AndroidCodeGenerator(
            base_package=BASE_PACKAGE,
            output_dir=output_dir
        )
        
        # 从 BASE_URL 中提取 server_base（用于生成文档链接）
        import re
        from urllib.parse import urlparse
        parsed_url = urlparse(BASE_URL)
        server_base = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        generated_files = generator.generate(
            api_tree, 
            category_filter=NODE_NAME,
            server_base=server_base
        )
        
        print("[OK] 代码生成完成")
        print()
        
        # 步骤6: 显示版本控制统计信息
        vc_info = generated_files.get("version_control", {})
        if vc_info:
            print("[步骤 6] 版本控制统计:")
            updated = vc_info.get('updated', 0)
            unchanged = vc_info.get('unchanged', 0)
            orphaned_count = vc_info.get('orphaned', 0)
            print(f"  - 已更新: {updated} 个文件")
            print(f"  - 未变化: {unchanged} 个文件")
            if orphaned_count > 0:
                print(f"  - 孤立文件: {orphaned_count} 个（接口文档中已不存在）")
                orphaned = vc_info.get('orphaned_files', [])
                if orphaned:
                    print(f"    孤立文件列表:")
                    for file_path in orphaned[:10]:  # 显示前10个
                        print(f"      - {file_path}")
                    if len(orphaned) > 10:
                        print(f"      ... 还有 {len(orphaned) - 10} 个文件")
                    print(f"    提示: 这些文件对应的 API 已从文档中删除，但仍存在于本地。")
                    print(f"    如需删除这些文件，请手动删除或使用清理工具。")
            print()
        
        # 步骤7: 显示生成的文件
        print("[步骤 7] 生成的文件:")
        
        if generated_files.get("services"):
            print(f"\n  [Service 接口] ({len(generated_files['services'])} 个文件):")
            for file_path in generated_files["services"]:
                file_name = Path(file_path).name
                print(f"    - {file_name}")
        
        if generated_files.get("entities"):
            print(f"\n  [实体类] ({len(generated_files['entities'])} 个文件):")
            for file_path in generated_files["entities"]:
                file_name = Path(file_path).name
                print(f"    - {file_name}")
        
        if generated_files.get("config"):
            print(f"\n  [配置文件] ({len(generated_files['config'])} 个文件):")
            for file_path in generated_files["config"]:
                file_name = Path(file_path).name
                print(f"    - {file_name}")
        
        print()
        
        # 步骤8: 显示使用提示
        print("[步骤 8] 下一步:")
        print(f"  1. 查看生成的文件: {output_dir}/")
        print(f"  2. 将生成的代码复制到你的 Android 项目中")
        print(f"  3. 添加依赖配置到 build.gradle.kts")
        print(f"  4. 根据实际 API 基础 URL 修改 OkHttpConfig.kt")
        print()
        
        print("=" * 70)
        print("[OK] 测试完成！")
        print("=" * 70)
        
        return 0
        
    except ShowDocNotFoundError as e:
        print(f"\n[ERROR] 错误: 未找到指定节点")
        print(f"   详情: {e}")
        print("\n提示: 请检查节点名称是否正确，或使用 None 获取全部节点")
        return 1
    except ShowDocAuthError as e:
        print(f"\n[ERROR] 错误: 认证失败")
        print(f"   详情: {e}")
        print("\n提示: 请检查 Cookie 是否有效，尝试重新登录 ShowDoc 获取新的 Cookie")
        return 1
    except KeyboardInterrupt:
        print("\n\n[WARN] 用户中断")
        return 1
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {type(e).__name__}")
        print(f"   详情: {e}")
        import traceback
        print("\n详细错误信息:")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

