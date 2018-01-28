@set i=0
set dirPrefix=%TEMP%\User Data

:checkUsableFolderName_UseIt
@set /A i+=1
@echo %i%
@set dir="%dirPrefix% %i%"
@mkdir %dir% ^
 && ( echo>%dir%\"First Run" && "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --incognito --user-data-dir=%dir% 
 goto mainProcessNotFound_check_lockfile 
 exit /b 1 )
@goto checkUsableFolderName_UseIt
@goto END

:mainProcessNotFound_check_lockfile
@ping -n 2 localhost > nul 
@if exist %dir%\lockfile (
 goto mainProcessNotFound_check_lockfile 
)
@rmdir /s /q %dir% 
@goto END

:END
exit /b 0
