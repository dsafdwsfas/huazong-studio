@echo off
chcp 65001 >/dev/null 2>&1
title Worker w10 - Backend Config Chinese
color 0A
echo.
echo =============================================
echo   Worker w10 - Backend Config Chinese
echo =============================================
echo.
cd /d D:\claude\bot-01\workspace\.worktrees\1.1-w10
echo Starting claude...
claude -p --dangerously-skip-permissions --verbose < D:\claude\bot-01\workspace\scripts\workers\w10-prompt.txt
echo.
echo Worker w10 DONE!
pause
