@echo off
chcp 65001 >/dev/null 2>&1
title Worker w6 - Chinese Nav Menu
color 0A
echo.
echo =============================================
echo   Worker w6 - Chinese Nav Menu
echo =============================================
echo.
cd /d D:\claude\bot-01\workspace\.worktrees\1.1-w6
echo Starting claude...
claude -p --dangerously-skip-permissions --verbose < D:\claude\bot-01\workspace\scripts\workers\w6-prompt.txt
echo.
echo Worker w6 DONE!
pause
