CD /d "%~dp0"

start "Server" cmd /K py -3 src/startserver.py -p 20000 -game "demo" -sname "FirstTry!!!" -debug

