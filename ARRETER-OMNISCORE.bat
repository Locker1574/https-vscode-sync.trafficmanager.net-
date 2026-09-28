@echo off
chcp 65001 >nul
title OMNISCORE - arrêt
cd /d "%~dp0"
echo Arrêt d'OMNISCORE...
docker compose down
echo OMNISCORE est arrêté. Vos comptes et données sont conservés.
pause
