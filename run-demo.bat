CD /d "%~dp0"

start "Server" cmd /K py -3 src/startserver.py -p 20000 -game "demo"
start "Client for Java" cmd /K py -3 src/startclient.py -p 20001 -sp 20000 -name "Java" -game "demo"
start "Client for Scout" cmd /K py -3 src/startclient.py -p 20002 -sp 20000 -name "Scout" -game "demo"
start "Client for River" cmd /K py -3 src/startclient.py -p 20003 -sp 20000 -name "River" -game "demo"

