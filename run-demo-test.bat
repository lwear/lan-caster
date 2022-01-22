CD /d "%~dp0"

start "Server" cmd /K py -3 src/startserver.py -p 20000 -game "demo" -test -pause 3
start "Client for Java" cmd /K py -3 src/startclient.py -p 20001 -sp 20000 -name "Java" -game "demo" -pause 0
start "Client for Scout" cmd /K py -3 src/startclient.py -p 20002 -sp 20000 -name "Scout" -game "demo" -pause 6
start "Client for River" cmd /K py -3 src/startclient.py -p 20003 -sp 20000 -name "River" -game "demo" -pause 9

