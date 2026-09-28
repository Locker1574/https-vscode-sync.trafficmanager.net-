@echo off
chcp 65001 >nul
title OMNISCORE - lancement
rem Se place dans le dossier de ce fichier (là où se trouve docker-compose.yml).
cd /d "%~dp0"

if not exist "docker-compose.yml" (
  echo [ERREUR] docker-compose.yml est introuvable dans %CD%
  echo Placez ce fichier dans le dossier OMNISCORE qui contient web, backend et prototype.
  pause
  exit /b 1
)

echo.
echo  === OMNISCORE ===
echo.
echo [1/4] Vérification de Docker...
docker info >nul 2>&1
if not errorlevel 1 goto docker_ok

echo Docker Desktop n'est pas démarré : tentative de lancement...
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
set /a essais=0
:attente_docker
timeout /t 5 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 goto docker_ok
set /a essais+=1
if %essais% LSS 24 goto attente_docker
echo.
echo [ERREUR] Docker ne répond pas après 2 minutes.
echo Ouvrez Docker Desktop, attendez "Engine running", puis relancez ce fichier.
echo Si Docker affiche une erreur : PowerShell administrateur, puis "wsl --update", puis redémarrez le PC.
pause
exit /b 1

:docker_ok
echo Docker est prêt.

echo [2/4] Préparation du secret de session...
if not exist ".omniscore-secret" powershell -NoProfile -Command "[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 })) | Set-Content -NoNewline -Path '.omniscore-secret'"
set /p SESSION_SECRET=<.omniscore-secret
if "%SESSION_SECRET%"=="" (
  echo [ERREUR] Impossible de créer le secret de session.
  pause
  exit /b 1
)

echo [3/4] Démarrage d'OMNISCORE (la première fois : 5 à 10 minutes)...
docker compose up --build -d
if errorlevel 1 (
  echo.
  echo [ERREUR] Le démarrage a échoué. Copiez le message ci-dessus et envoyez-le à Claude.
  pause
  exit /b 1
)

echo [4/4] Attente du site (jusqu'à 10 minutes)...
powershell -NoProfile -Command "$ok=$false; for($i=0;$i -lt 120;$i++){ try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 http://localhost:3000/api/health; if($r.StatusCode -eq 200){$ok=$true; break} } catch {}; Start-Sleep -Seconds 5 }; if(-not $ok){ exit 1 }"
if errorlevel 1 (
  echo.
  echo [ERREUR] Le site ne répond pas. Journal : docker compose logs web
  pause
  exit /b 1
)

echo.
echo OMNISCORE est prêt : http://localhost:3000
echo Les matchs apparaissent après la première synchronisation (1 à 2 minutes).
echo Pour arrêter : double-cliquez sur ARRETER-OMNISCORE.bat
start "" http://localhost:3000
pause
