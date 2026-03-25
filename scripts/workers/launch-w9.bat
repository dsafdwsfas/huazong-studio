@echo off
chcp 65001 >/dev/null 2>&1
title Worker w9 - Login Page Redesign
color 0A
echo.
echo =============================================
echo   Worker w9 - Login Page Redesign
echo =============================================
echo.
cd /d D:\claude\bot-01\workspace\.worktrees\1.1-w9
echo Starting claude...
claude -p --dangerously-skip-permissions --verbose < D:\claude\bot-01\workspace\scripts\workers\w9-prompt.txt
echo.
echo Worker w9 DONE!
pause
