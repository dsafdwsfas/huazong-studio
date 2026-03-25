@echo off
chcp 65001 >/dev/null 2>&1
title Worker w2 - Brand i18n Files
color 0A
echo.
echo =============================================
echo   Worker w2 - Brand i18n Files
echo =============================================
echo.
cd /d D:\claude\bot-01\workspace\.worktrees\1.1-w2
echo Starting claude...
claude -p --dangerously-skip-permissions --verbose < D:\claude\bot-01\workspace\scripts\workers\w2-prompt.txt
echo.
echo Worker w2 DONE!
pause
