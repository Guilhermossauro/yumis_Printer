@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

echo.
echo === Yumis' Printer - Push Step by Step ===
echo This script creates many commits (one file per commit) and pushes each commit.
echo.

where git >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Git is not installed or not in PATH.
    pause
    exit /b 1
)

if not exist ".git" (
    echo [INFO] Initializing git repository...
    git init
    if errorlevel 1 (
        echo [ERROR] Could not initialize git repository.
        pause
        exit /b 1
    )
)

for /f "delims=" %%A in ('git config user.name 2^>nul') do set "GIT_USER=%%A"
for /f "delims=" %%A in ('git config user.email 2^>nul') do set "GIT_EMAIL=%%A"

if not defined GIT_USER (
    set /p GIT_USER=Git user.name: 
    if "%GIT_USER%"=="" (
        echo [ERROR] user.name is required.
        pause
        exit /b 1
    )
    git config user.name "%GIT_USER%"
)

if not defined GIT_EMAIL (
    set /p GIT_EMAIL=Git user.email: 
    if "%GIT_EMAIL%"=="" (
        echo [ERROR] user.email is required.
        pause
        exit /b 1
    )
    git config user.email "%GIT_EMAIL%"
)

set /p REMOTE_URL=GitHub remote URL (example: https://github.com/user/repo.git): 
if "%REMOTE_URL%"=="" (
    echo [ERROR] Remote URL is required.
    pause
    exit /b 1
)

set /p BRANCH_NAME=Branch name [main]: 
if "%BRANCH_NAME%"=="" set "BRANCH_NAME=main"

echo.
echo [INFO] Using branch: %BRANCH_NAME%

git checkout -B "%BRANCH_NAME%"
if errorlevel 1 (
    echo [ERROR] Could not checkout branch %BRANCH_NAME%.
    pause
    exit /b 1
)

git remote get-url origin >nul 2>nul
if errorlevel 1 (
    git remote add origin "%REMOTE_URL%"
) else (
    git remote set-url origin "%REMOTE_URL%"
)

set /a COMMIT_COUNT=0

for /r %%F in (*) do (
    set "ABS=%%~fF"
    set "REL=!ABS:%CD%\=!"

    if /I not "!REL:~0,5!"==".git\" (
        git check-ignore -q "!REL!" >nul 2>nul
        if errorlevel 1 (
            git add -- "!REL!"

            git diff --cached --quiet -- "!REL!" >nul 2>nul
            if errorlevel 1 (
                set /a COMMIT_COUNT+=1
                git commit -m "chore: add !REL!" -- "!REL!"
                if errorlevel 1 (
                    echo [WARN] Failed to commit !REL!
                ) else (
                    echo [OK] Commit !COMMIT_COUNT!: !REL!
                    git push -u origin "%BRANCH_NAME%"
                    if errorlevel 1 (
                        echo [WARN] Push failed after commit !COMMIT_COUNT!.
                        echo [INFO] You can run: git push -u origin %BRANCH_NAME%
                    )
                )
            )
        )
    )
)

echo.
if %COMMIT_COUNT% EQU 0 (
    echo [INFO] Nothing new to commit.
) else (
    echo [DONE] %COMMIT_COUNT% commit(s) created.
)

echo.
echo Finished.
pause
exit /b 0
