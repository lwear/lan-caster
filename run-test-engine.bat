CD /d "%~dp0"

start "Server" cmd /K py -3 src/startserver.py -p 20000 -game "test-engine"
start "Client" cmd /K py -3 src/startclient.py -p 20001 -sp 20000 -name "Bob" -game "test-engine"

