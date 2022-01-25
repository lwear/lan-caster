CD /d "%~dp0"

start "Client" cmd /K py -3 src/startclient.py -connect "MyGameServer"

