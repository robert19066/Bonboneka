@echo off
setlocal EnableDelayedExpansion
title Bonboneka Installer

:: ─────────────────────────────────────────────
::  Bonboneka Installer  (Windows)
:: ─────────────────────────────────────────────

:: Colours via ANSI (requires Windows 10 1511+ / Windows Terminal)
for /f %%A in ('echo prompt $E^| cmd') do set "ESC=%%A"
set "RESET=%ESC%[0m"
set "BOLD=%ESC%[1m"
set "DIM=%ESC%[2m"
set "RED=%ESC%[31m"
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "CYAN=%ESC%[36m"

:: ── Header ────────────────────────────────────
echo.
echo %BOLD%%CYAN%+--------------------------------------+%RESET%
echo %BOLD%%CYAN%^|        Bonboneka  Installer          ^|%RESET%
echo %BOLD%%CYAN%^|   Ver 2.0 "Choco-Milk-Sugar Goodness"  ^|%RESET%
echo %BOLD%%CYAN%+--------------------------------------+%RESET%
echo.

:: ── Preflight checks ──────────────────────────
echo %BOLD%  Checking prerequisites...%RESET%
echo.

:: Python
set "PYTHON="
where python3 >nul 2>&1 && set "PYTHON=python3"
if not defined PYTHON (
    where python >nul 2>&1 && set "PYTHON=python"
)
if not defined PYTHON (
    echo %RED%  X  Python not found.%RESET%
    echo      Install Python 3.8+ from https://www.python.org/ and try again.
    goto :fail
)
for /f "tokens=*" %%V in ('!PYTHON! -c "import sys; print(\"%%d.%%d\" %% sys.version_info[:2])"') do (
    echo %GREEN%  OK  Python %%V  (!PYTHON!)%RESET%
)

:: pip
!PYTHON! -m pip --version >nul 2>&1
if errorlevel 1 (
    echo %RED%  X  pip not found.%RESET%
    echo      Run:  !PYTHON! -m ensurepip --upgrade
    goto :fail
)
echo %GREEN%  OK  pip found%RESET%

:: Node.js (optional)
set "HAS_NODE=0"
where node >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%V in ('node --version') do (
        echo %GREEN%  OK  Node.js %%V%RESET%
    )
    set "HAS_NODE=1"
) else (
    echo %YELLOW%  !   Node.js not found — PWA support (--pwa) will not be available.%RESET%
    echo %YELLOW%      Install Node.js 14+ from https://nodejs.org/ to enable it.%RESET%
)

:: npm
if "!HAS_NODE!"=="1" (
    where npm >nul 2>&1
    if errorlevel 1 (
        echo %YELLOW%  !   npm not found PWA support will not be available.%RESET%
        set "HAS_NODE=0"
    )
)

:: ── Menu ──────────────────────────────────────
echo.
echo   %BOLD%How would you like to install Bonboneka?%RESET%
echo.
echo   %CYAN%1%RESET%  setup.py  %DIM%(editable install — for contributors / local dev)%RESET%
echo   %CYAN%2%RESET%  pip       %DIM%(standard install from PyPI)%RESET%
echo   %CYAN%Q%RESET%  Quit
echo.

:menu_loop
set "CHOICE="
set /p "CHOICE=  Enter choice [1/2/Q]: "

if /i "!CHOICE!"=="q" (
    echo.
    echo   %CYAN%Cancelled.%RESET%
    goto :end
)
if "!CHOICE!"=="1" goto :do_setup
if "!CHOICE!"=="2" goto :do_pip
echo %YELLOW%  !   Invalid choice — enter 1, 2, or Q.%RESET%
goto :menu_loop


:: ── setup.py path ─────────────────────────────
:do_setup
call :install_bubblewrap
echo.
echo %BOLD%  Installing Bonboneka via setup.py (editable)...%RESET%
if not exist setup.py (
    if not exist pyproject.toml (
        echo %RED%  X  setup.py / pyproject.toml not found.%RESET%
        echo      Run this installer from the project root directory.
        goto :fail
    )
)
!PYTHON! -m pip install -e . -q
if errorlevel 1 goto :fail
echo %GREEN%  OK  Bonboneka installed (editable)%RESET%
goto :success

:: ── pip path ──────────────────────────────────
:do_pip
call :install_bubblewrap
echo.
echo %BOLD%  Installing Bonboneka via pip...%RESET%
!PYTHON! -m pip install bonboneka -q
if errorlevel 1 goto :fail
echo %GREEN%  OK  Bonboneka installed%RESET%
goto :success

:: ── Outcomes ──────────────────────────────────
:success
echo.
echo %BOLD%%GREEN%  +-------------------------------------+%RESET%
echo %BOLD%%GREEN%  ^|   Installation complete!           ^|%RESET%
echo %BOLD%%GREEN%  +-------------------------------------+%RESET%
echo.
echo   %CYAN%Run %BOLD%bomk --help%RESET%%CYAN% to get started.%RESET%
echo.
pause
goto :end

:fail
echo.
echo %RED%  Installation failed. See errors above.%RESET%
echo.
pause
exit /b 1

:end
endlocal