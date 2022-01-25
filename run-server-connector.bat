CD /d "%~dp0"

start "Server" cmd /K py -3 src/startserver.py -register "MyGameServer"

