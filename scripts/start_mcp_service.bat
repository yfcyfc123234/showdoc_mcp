@echo off
chcp 65001 >nul 2>&1
echo 正在启动 ShowDoc MCP 服务...
REM 切换到项目根目录（脚本在 scripts 文件夹中，需要回到上一级）
cd /d "%~dp0\.."
python -m mcp_showdoc.mcp_server
pause

