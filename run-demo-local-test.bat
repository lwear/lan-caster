CD /d "%~dp0"

start "Server" cmd /K py -3 src/startserver.py -test -pause 3
start "Client for Java" cmd /K py -3 src/startclient.py -player "Java" -pause 0
start "Client for Scout" cmd /K py -3 src/startclient.py -player "Scout" -pause 6
start "Client for River" cmd /K py -3 src/startclient.py -player "River" -pause 9

