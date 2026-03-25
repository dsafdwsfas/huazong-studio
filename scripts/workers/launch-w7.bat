@echo off
chcp 65001 >/dev/null 2>&1
title Worker w7 - Chinese Forms Dialogs
color 0A
echo.
echo =============================================
echo   Worker w7 - Chinese Forms Dialogs
echo =============================================
echo.
cd /d D:\claude\bot-01\workspace\.worktrees\1.1-w7
echo Starting claude...
claude -p --dangerously-skip-permissions --verbose < D:\claude\bot-01\workspace\scripts\workers\w7-prompt.txt
echo.
echo Worker w7 DONE!
pause
