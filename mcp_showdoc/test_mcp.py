"""
MCP ShowDoc 测试脚本
测试新增的两个方法：fetch_node_detail_info 和 fetch_node_cookie

使用方法：
1. 在 mcp_showdoc 目录内运行：python test_mcp.py
2. 从项目根目录运行：python -m mcp_showdoc.test_mcp
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

# 添加父目录到路径（如果在 mcp_showdoc 目录内运行）
if Path(__file__).parent.name == 'mcp_showdoc':
    sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_showdoc.server import (
    showdoc_fetch_node_tree,
    get_node_detail_info,
    get_node_cookie,
)


# ========== 配置参数 ==========
BASE_URL = "https://www.showdoc.com.cn/2598847052437483/11559024030603677"
COOKIE = None  # 可选，如果提供则使用 Cookie 认证
PASSWORD = "123456"  # 默认密码，如果未提供 COOKIE 则使用密码自动登录

# 要查询详细信息的节点名称（默认为"用户信息"）
TARGET_NODE_NAME = "用户信息"  # 可以修改为其他节点名称，如 "订单"、"商品" 等


def print_node_tree(node_tree, indent=0):
    """递归打印节点树结构"""
    prefix = "  " * indent
    
    if isinstance(node_tree, dict):
        if "cat_name" in node_tree:
            # 这是一个分类节点
            cat_name = node_tree.get("cat_name", "")
            cat_id = node_tree.get("cat_id", "")
            print(f"{prefix}📁 {cat_name} (cat_id: {cat_id})")
            
            # 打印页面
            pages = node_tree.get("pages", [])
            for page in pages:
                page_title = page.get("page_title", "")
                page_id = page.get("page_id", "")
                print(f"{prefix}  📄 {page_title} (page_id: {page_id})")
            
            # 递归打印子分类
            children = node_tree.get("children", [])
            for child in children:
                print_node_tree(child, indent + 1)
        elif "categories" in node_tree:
            # 这是根节点，包含所有分类
            print(f"{prefix}📦 项目: {node_tree.get('item_info', {}).get('item_name', '')}")
            categories = node_tree.get("categories", [])
            for cat in categories:
                print_node_tree(cat, indent + 1)


def print_node_detail(node_info):
    """打印节点详细信息"""
    print("\n" + "=" * 70)
    print("节点详细信息")
    print("=" * 70)
    
    cat_name = node_info.get("cat_name", "")
    cat_id = node_info.get("cat_id", "")
    print(f"\n分类名称: {cat_name}")
    print(f"分类 ID: {cat_id}")
    
    pages = node_info.get("pages", [])
    print(f"\n页面数量: {len(pages)}")
    
    for i, page in enumerate(pages, 1):
        print(f"\n--- 页面 {i} ---")
        page_title = page.get("page_title", "")
        page_id = page.get("page_id", "")
        print(f"标题: {page_title}")
        print(f"页面 ID: {page_id}")
        
        api_info = page.get("api_info")
        if api_info:
            print(f"类型: API 接口")
            print(f"方法: {api_info.get('method', 'N/A')}")
            print(f"URL: {api_info.get('url', 'N/A')}")
            print(f"标题: {api_info.get('title', 'N/A')}")
            if api_info.get('description'):
                print(f"描述: {api_info.get('description')}")
            
            # 打印请求信息
            request = api_info.get('request')
            if request:
                print(f"\n请求参数:")
                if isinstance(request, dict):
                    params = request.get('params') or request.get('body') or {}
                    if params:
                        print(json.dumps(params, ensure_ascii=False, indent=2))
                    else:
                        print("  无请求参数")
                else:
                    print(f"  {request}")
            
            # 打印响应信息
            response = api_info.get('response')
            if response:
                print(f"\n响应数据:")
                if isinstance(response, dict):
                    print(json.dumps(response, ensure_ascii=False, indent=2))
                else:
                    print(f"  {response}")
        else:
            # 检查是否有页面内容
            page_content = page.get("page_content")
            if page_content:
                print(f"类型: 普通页面（非API）")
                print(f"内容: {json.dumps(page_content, ensure_ascii=False, indent=2)[:200]}...")
            else:
                print(f"类型: 普通页面（无详细信息）")


def main():
    """主测试函数"""
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
    
    print("=" * 70)
    print("MCP ShowDoc 测试")
    print("=" * 70)
    print()
    print(f"测试 URL: {BASE_URL}")
    print(f"目标节点: {TARGET_NODE_NAME}")
    print()
    sys.stdout.flush()
    
    try:
        # 步骤1: 获取 Cookie 信息
        print("[步骤 1] 获取 Cookie 信息...")
        cookie_result = get_node_cookie(
            base_url=BASE_URL,
            cookie=COOKIE,
            password=PASSWORD,
        )
        
        if not cookie_result.get("ok"):
            print(f"[失败] {cookie_result.get('error')}")
            return
        
        cookie = cookie_result.get("cookie")
        from_cache = cookie_result.get("from_cache", False)
        print(f"[OK] 成功获取 Cookie")
        print(f"  - 来源: {'缓存' if from_cache else '新登录'}")
        print(f"  - Cookie: {cookie[:50]}..." if cookie and len(cookie) > 50 else f"  - Cookie: {cookie}")
        print()
        
        # 步骤2: 获取所有节点信息
        print("[步骤 2] 获取所有节点信息...")
        try:
            node_tree_result = showdoc_fetch_node_tree(
                base_url=BASE_URL,
                cookie=cookie,
                password=PASSWORD,
            )
            
            if not node_tree_result.get("ok"):
                error_msg = node_tree_result.get('error', '未知错误')
                print(f"[失败] {error_msg}")
                print("\n提示: Cookie 可能已过期，尝试重新登录...")
                # 尝试不使用 Cookie，直接使用密码登录
                print("  重新尝试使用密码登录...")
                node_tree_result = showdoc_fetch_node_tree(
                    base_url=BASE_URL,
                    cookie=None,
                    password=PASSWORD,
                )
                if not node_tree_result.get("ok"):
                    error_msg2 = node_tree_result.get('error', '未知错误')
                    print(f"[失败] {error_msg2}")
                    print("\n详细错误信息:")
                    print(f"  - 错误类型: {type(error_msg2).__name__ if hasattr(error_msg2, '__class__') else '字符串'}")
                    print(f"  - 完整错误: {error_msg2}")
                    return
                print("[OK] 使用密码登录成功")
        except Exception as e:
            print(f"[失败] 发生异常: {e}")
            print(f"异常类型: {type(e).__name__}")
            import traceback
            print("\n完整堆栈跟踪:")
            traceback.print_exc()
            return
        
        node_tree = node_tree_result.get("node_tree")
        print("[OK] 成功获取节点树")
        print()
        
        # 显示节点树结构
        print("[步骤 3] 节点树结构:")
        print_node_tree(node_tree)
        print()
        
        # 步骤4: 查询指定节点的详细信息
        print(f"[步骤 4] 查询节点 '{TARGET_NODE_NAME}' 的详细信息...")
        detail_result = get_node_detail_info(
            base_url=BASE_URL,
            node_name=TARGET_NODE_NAME,
            cookie=cookie,
            password=PASSWORD,
            snapshot_path=None,  # 自动查找最新快照
        )
        
        if not detail_result.get("ok"):
            print(f"[失败] {detail_result.get('error')}")
            print("\n提示: 请检查节点名称是否正确，或尝试使用其他节点名称")
            return
        
        node_info = detail_result.get("node_info")
        from_cache_detail = detail_result.get("from_cache", False)
        snapshot_path = detail_result.get("snapshot_path")
        
        print("[OK] 成功获取节点详细信息")
        print(f"  - 数据来源: {'缓存' if from_cache_detail else '新抓取'}")
        if snapshot_path:
            print(f"  - 快照路径: {snapshot_path}")
        print()
        
        # 显示节点详细信息
        print_node_detail(node_info)
        print()
        
        print("=" * 70)
        print("测试完成！")
        print("=" * 70)
        sys.stdout.flush()
        
    except KeyboardInterrupt:
        print("\n\n[中断] 用户中断测试")
        sys.stdout.flush()
    except Exception as e:
        print(f"\n[错误] 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()


if __name__ == "__main__":
    main()

