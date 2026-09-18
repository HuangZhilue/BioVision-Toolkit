@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 检查是否安装了 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8 或以上版本，并勾选 "Add to PATH"！
    pause
    exit /b
)

REM 检查虚拟环境
if not exist venv (
    echo ==================================================
    echo [信息] 首次运行，正在创建虚拟环境 (大约需要 1-2 分钟)...
    python -m venv venv
    echo [信息] 正在激活虚拟环境并安装依赖...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo ==================================================
) else (
    call venv\Scripts\activate.bat
)

:MENU
cls
echo ==================================================
echo      iNaturalist 离线鸟类识别系统 控制台
echo ==================================================
echo [1] 🚀 启动 Web 服务 (启动 app.py)
echo [2] 🔄 重新构建终极数据库 (执行 build_database_perfect.py)
echo [3] 🖼️ 下载缺失鸟类图片 (执行 download_images.py)
echo [0] ❌ 退出
echo ==================================================
set /p choice="请输入你的选择 (0-3): "

if "%choice%"=="1" goto START_WEB
if "%choice%"=="2" goto BUILD_DB
if "%choice%"=="3" goto DOWNLOAD_IMG
if "%choice%"=="0" goto EOF
goto MENU

:START_WEB
echo.
echo ==================================================
echo [成功] 服务即将启动...
echo [提示] 启动成功后，请在浏览器中打开: http://127.0.0.1:8000/bioclip.html
echo [提示] 不要关闭此黑色窗口！关闭窗口即停止服务。
echo ==================================================
python app.py
pause
goto MENU

:BUILD_DB
echo.
echo ==================================================
echo [信息] 正在启动终极数据库重构脚本...
echo [注意] 此过程需要耗时几分钟，请耐心等待。
echo ==================================================
python build_database_perfect.py
echo.
echo [完成] 数据库构建结束。按任意键返回主菜单...
pause >nul
goto MENU

:DOWNLOAD_IMG
echo.
echo ==================================================
echo [信息] 正在启动图片下载脚本...
echo [注意] 将自动跳过已存在的图片，仅下载缺失图片。
echo ==================================================
python download_images.py
echo.
echo [完成] 图片下载结束。按任意键返回主菜单...
pause >nul
goto MENU

:EOF
exit /b
