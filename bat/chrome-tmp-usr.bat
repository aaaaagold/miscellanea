@set i=0
set dirPrefix=%TEMP%\User Data

:J1
@set /A i+=1
@echo %i%
@set dir="%dirPrefix% %i%"
@mkdir %dir% ^
 && ( echo>%dir%\"First Run" && "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --incognito --user-data-dir=%dir% 
 ping -n 2 localhost > nul 
 rmdir /s /q %dir% 
 exit )
@goto J1
