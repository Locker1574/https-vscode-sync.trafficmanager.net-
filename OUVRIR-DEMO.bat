@echo off
rem Ouvre l'application en un seul fichier, sans Docker ni installation.
cd /d "%~dp0"
start "" "%~dp0prototype\omniscore.html"
