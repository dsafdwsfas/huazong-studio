@echo off
chcp 65001 >/dev/null 2>&1
title Worker w3 - Brand Backend API
color 0A
echo.
echo =============================================
echo   Worker w3 - Brand Backend API
echo =============================================
echo.
cd /d D:\claude\bot-01\workspace\.worktrees\1.1-w3
echo Starting claude...
claude -p --dangerously-skip-permissions --verbose < D:\claude\bot-01\workspace\scripts\workers\w3-prompt.txt
echo.
echo Worker w3 DONE!
pause
