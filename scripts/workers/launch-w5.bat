@echo off
chcp 65001 >/dev/null 2>&1
title Worker w5 - Brand Meta Info
color 0A
echo.
echo =============================================
echo   Worker w5 - Brand Meta Info
echo =============================================
echo.
cd /d D:\claude\bot-01\workspace\.worktrees\1.1-w5
echo Starting claude...
claude -p --dangerously-skip-permissions --verbose < D:\claude\bot-01\workspace\scripts\workers\w5-prompt.txt
echo.
echo Worker w5 DONE!
pause
