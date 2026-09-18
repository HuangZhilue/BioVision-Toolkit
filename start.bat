@echo off
chcp 65001 >nul
echo ==================================================
echo   AI 鸟类识别系统 - 本地一键启动脚本 (无需 Docker)
echo ==================================================

REM 检查是否安装了 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8 或以上版本，并勾选 "Add to PATH"！
    pause
    exit /b
)

REM 检查虚拟环境
if not exist venv (
    echo [信息] 首次运行，正在创建虚拟环境 (大约需要 1-2 分钟)...
    python -m venv venv
)

REM 激活虚拟环境
echo [信息] 正在激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo [信息] 检查并安装依赖 (首次运行可能需要下载较大模型库，请耐心等待)...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

REM 启动应用
echo ==================================================
echo [成功] 服务即将启动...
echo [提示] 启动成功后，请在浏览器中打开: http://127.0.0.1:8000
echo [提示] 不要关闭此黑色窗口！关闭窗口即停止服务。
echo ==================================================
python app.py

pause
