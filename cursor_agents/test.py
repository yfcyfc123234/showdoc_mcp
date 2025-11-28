"""
Cursor Cloud Agents API 客户端测试脚本
统一测试文件，支持所有功能

使用方法：
1. 在 cursor_agents 目录内运行：python test.py
2. 从项目根目录运行：python -m cursor_agents.test
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

# 添加父目录到路径（如果在 cursor_agents 目录内运行）
if Path(__file__).parent.name == 'cursor_agents':
    sys.path.insert(0, str(Path(__file__).parent.parent))

from cursor_agents import CursorAgentsClient


# ========== 配置参数（请修改为你的实际参数）==========
# API Key（首次使用时需要设置）
API_KEY = "key_8a30cae728bbd37b26439c4309f669a23bc188c41a4c6ecaf9e6caa762e8baad"  # 例如: "your_cursor_api_key_here"

# 测试用的 Agent ID（用于测试获取状态、会话等功能）
# 可以从 list_cursor_agents_tool 获取
TEST_AGENT_ID = None  # 例如: "bc_abc123"

# 是否显示详细信息（True/False）
SHOW_DETAILS = True

# 是否自动设置 API Key（如果未设置）
AUTO_SET_API_KEY = False
# ====================================================


def print_user_info(user_info):
    """打印用户信息"""
    if not user_info:
        print("  - 用户信息: 未获取")
        return
    
    print("  - 用户信息:")
    print(f"    API Key 名称: {user_info.get('apiKeyName', 'N/A')}")
    print(f"    创建时间: {user_info.get('createdAt', 'N/A')}")
    print(f"    用户邮箱: {user_info.get('userEmail', 'N/A')}")


def print_agent_summary(agent):
    """打印代理摘要信息"""
    agent_id = agent.get('id', 'N/A')
    name = agent.get('name', 'N/A')
    status = agent.get('status', 'N/A')
    
    print(f"    - [{status}] {name} (ID: {agent_id})")
    
    if SHOW_DETAILS:
        source = agent.get('source', {})
        target = agent.get('target', {})
        summary = agent.get('summary', '')
        
        if source:
            repo = source.get('repository', 'N/A')
            ref = source.get('ref', 'N/A')
            print(f"      源仓库: {repo} (ref: {ref})")
        
        if target:
            branch = target.get('branchName', 'N/A')
            pr_url = target.get('prUrl', '')
            if pr_url:
                print(f"      目标分支: {branch}")
                print(f"      PR: {pr_url}")
            else:
                print(f"      目标分支: {branch}")
        
        if summary:
            summary_short = summary[:100] + "..." if len(summary) > 100 else summary
            print(f"      摘要: {summary_short}")
        
        created_at = agent.get('createdAt', '')
        if created_at:
            print(f"      创建时间: {created_at}")


def main():
    """主测试函数"""
    print("=" * 70)
    print("Cursor Cloud Agents API 客户端测试")
    print("=" * 70)
    print()
    
    try:
        # 步骤1: 初始化客户端
        print("[步骤 1] 初始化客户端...")
        
        # 如果提供了 API_KEY，先设置
        if API_KEY:
            try:
                # 使用提供的 API_KEY 创建客户端（临时使用，不依赖缓存）
                client = CursorAgentsClient(api_key=API_KEY)
                # 设置并缓存 API Key（会获取用户信息）
                result = client.set_api_key(API_KEY, fetch_user_info=True)
                print("[OK] API Key 已设置并缓存")
                if result.get('user_info'):
                    print_user_info(result['user_info'])
                elif result.get('warning'):
                    print(f"  - 警告: {result['warning']}")
            except ValueError as e:
                print(f"[失败] {e}")
                return 1
            except Exception as e:
                print(f"[失败] 设置 API Key 时出错: {e}")
                return 1
        else:
            # 尝试从缓存加载
            try:
                client = CursorAgentsClient()
                print("[OK] 从缓存加载 API Key")
                
                # 尝试获取缓存的用户信息
                user_info = client.get_cached_user_info()
                if user_info:
                    print_user_info(user_info)
                else:
                    print("  - 提示: 未找到缓存的用户信息，将尝试获取...")
                    try:
                        user_info = client.get_api_key_info()
                        print_user_info(user_info)
                    except Exception as e:
                        print(f"  - 警告: 获取用户信息失败: {e}")
            except ValueError as e:
                print(f"[失败] {e}")
                if AUTO_SET_API_KEY:
                    print("  - 提示: 请设置 API_KEY 配置参数")
                else:
                    print("  - 提示: 请设置 API_KEY 配置参数，或使用 set_cursor_api_key_tool 工具设置")
                return 1
        
        print()
        
        # 步骤2: 获取 API Key 信息
        print("[步骤 2] 获取 API Key 信息...")
        try:
            api_key_info = client.get_api_key_info()
            print("[OK] 成功获取")
            print_user_info(api_key_info)
        except Exception as e:
            print(f"[失败] {e}")
        print()
        
        # 步骤3: 列出推荐模型
        print("[步骤 3] 获取推荐模型列表...")
        try:
            models_result = client.list_models()
            models = models_result.get('models', [])
            print(f"[OK] 成功获取 ({len(models)} 个模型)")
            if models:
                print("  - 推荐模型:")
                for model in models:
                    print(f"    - {model}")
            else:
                print("  - 未找到推荐模型")
        except Exception as e:
            print(f"[失败] {e}")
        print()
        
        # 步骤4: 列出所有代理
        agents = []
        print("[步骤 4] 列出所有云端代理...")
        try:
            agents_result = client.list_agents(limit=10)
            agents = agents_result.get('agents', [])
            next_cursor = agents_result.get('nextCursor')
            
            print(f"[OK] 成功获取 ({len(agents)} 个代理)")
            
            if agents:
                print("  - 代理列表:")
                for agent in agents:
                    print_agent_summary(agent)
                    print()
                
                if next_cursor:
                    print(f"  - 提示: 还有更多代理，使用 cursor={next_cursor} 获取下一页")
            else:
                print("  - 未找到任何代理")
        except Exception as e:
            print(f"[失败] {e}")
        print()
        
        # 步骤5: 获取代理状态（如果有测试用的 Agent ID）
        test_agent_id = TEST_AGENT_ID
        if not test_agent_id and agents:
            test_agent_id = agents[0].get('id') if agents else None
        
        if test_agent_id and not TEST_AGENT_ID:
            print(f"  - 提示: 将使用第一个代理 (ID: {test_agent_id}) 进行后续测试")
            print()
        
        if test_agent_id:
            print(f"[步骤 5] 获取代理状态 (ID: {test_agent_id})...")
            try:
                agent_status = client.get_agent_status(test_agent_id)
                print("[OK] 成功获取")
                print(f"  - 代理名称: {agent_status.get('name', 'N/A')}")
                print(f"  - 状态: {agent_status.get('status', 'N/A')}")
                
                if SHOW_DETAILS:
                    source = agent_status.get('source', {})
                    target = agent_status.get('target', {})
                    summary = agent_status.get('summary', '')
                    
                    if source:
                        repo = source.get('repository', 'N/A')
                        ref = source.get('ref', 'N/A')
                        print(f"  - 源仓库: {repo} (ref: {ref})")
                    
                    if target:
                        branch = target.get('branchName', 'N/A')
                        url = target.get('url', '')
                        pr_url = target.get('prUrl', '')
                        print(f"  - 目标分支: {branch}")
                        if url:
                            print(f"  - 查看链接: {url}")
                        if pr_url:
                            print(f"  - PR 链接: {pr_url}")
                    
                    if summary:
                        print(f"  - 摘要: {summary}")
            except Exception as e:
                print(f"[失败] {e}")
            print()
            
            # 步骤6: 获取代理会话（如果代理已完成）
            if agent_status.get('status') in ['FINISHED', 'RUNNING']:
                print(f"[步骤 6] 获取代理会话 (ID: {test_agent_id})...")
                try:
                    conversation = client.get_agent_conversation(test_agent_id)
                    messages = conversation.get('messages', [])
                    print(f"[OK] 成功获取 ({len(messages)} 条消息)")
                    
                    if SHOW_DETAILS and messages:
                        print("  - 会话消息:")
                        max_show = 5
                        for i, msg in enumerate(messages[:max_show], 1):
                            msg_type = msg.get('type', 'unknown')
                            text = msg.get('text', '')
                            text_short = text[:100] + "..." if len(text) > 100 else text
                            
                            if msg_type == 'user_message':
                                print(f"    {i}. [用户] {text_short}")
                            elif msg_type == 'assistant_message':
                                print(f"    {i}. [助手] {text_short}")
                            else:
                                print(f"    {i}. [{msg_type}] {text_short}")
                        
                        if len(messages) > max_show:
                            print(f"    ... 还有 {len(messages) - max_show} 条消息")
                except Exception as e:
                    print(f"[失败] {e}")
                print()
        else:
            print("[步骤 5] 跳过（未提供测试用的 Agent ID）")
            print()
        
        # 步骤7: 列出 GitHub 仓库（可选，有速率限制）
        print("[步骤 7] 列出 GitHub 仓库（可选，有严格速率限制）...")
        print("  - 提示: 此 API 有严格速率限制（1 次/用户/分钟，30 次/用户/小时）")
        print("  - 提示: 如需测试，请取消下面的注释")
        # try:
        #     repos_result = client.list_repositories()
        #     repositories = repos_result.get('repositories', [])
        #     print(f"[OK] 成功获取 ({len(repositories)} 个仓库)")
        #     if SHOW_DETAILS and repositories:
        #         print("  - 仓库列表（前5个）:")
        #         for repo in repositories[:5]:
        #             owner = repo.get('owner', 'N/A')
        #             name = repo.get('name', 'N/A')
        #             repo_url = repo.get('repository', 'N/A')
        #             print(f"    - {owner}/{name}")
        #             print(f"      URL: {repo_url}")
        #     if len(repositories) > 5:
        #         print(f"    ... 还有 {len(repositories) - 5} 个仓库")
        # except Exception as e:
        #     print(f"[失败] {e}")
        print("  - 已跳过（如需测试请取消代码中的注释）")
        print()
        
        # 步骤8: 显示缓存信息
        print("[步骤 8] 缓存信息:")
        api_key_file = client.API_KEY_FILE
        user_info_file = client.USER_INFO_FILE
        
        print(f"  - API Key 缓存: {api_key_file}")
        if api_key_file.exists():
            print("    ✓ 已缓存")
        else:
            print("    ✗ 未缓存")
        
        print(f"  - 用户信息缓存: {user_info_file}")
        if user_info_file.exists():
            print("    ✓ 已缓存")
            if SHOW_DETAILS:
                try:
                    with open(user_info_file, 'r', encoding='utf-8') as f:
                        cached_info = json.load(f)
                        print(f"    - API Key 名称: {cached_info.get('apiKeyName', 'N/A')}")
                        print(f"    - 用户邮箱: {cached_info.get('userEmail', 'N/A')}")
                except Exception:
                    pass
        else:
            print("    ✗ 未缓存")
        print()
        
        print("=" * 70)
        print("[OK] 测试完成！")
        print("=" * 70)
        print()
        print("💡 提示:")
        print("  - API Key 已缓存到: ~/.cursor/mcp_cache/api_key.json")
        print("  - 用户信息已缓存到: output/.cursor_api_key_info.json")
        print("  - 后续使用无需重复设置 API Key")
        
        return 0
        
    except ValueError as e:
        print()
        print("=" * 70)
        print("❌ 错误: API Key 相关错误")
        print("=" * 70)
        print(f"\n错误详情: {e}")
        print("\n💡 解决方案:")
        print("  1. 检查 API_KEY 配置是否正确")
        print("  2. 访问 https://cursor.com/settings 获取 API Key")
        print("  3. 使用 set_cursor_api_key_tool MCP 工具设置 API Key")
        return 1
    except RuntimeError as e:
        print()
        print("=" * 70)
        print("❌ 错误: API 请求失败")
        print("=" * 70)
        print(f"\n错误详情: {e}")
        print("\n💡 解决方案:")
        print("  1. 检查网络连接")
        print("  2. 检查 API Key 是否有效")
        print("  3. 检查 API 端点是否可访问")
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

