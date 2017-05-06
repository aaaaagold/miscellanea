
@if [%1] == [] goto argErr
@if [%2] == [] goto argErr
@ping -w 999 -n 2 localhost > nul || goto pingERR

@echo use ctrl-c to copy the file immediately and exit
@set syncitv=31
@set waititv=31

:loop
@ping -w 999 -n %syncitv% localhost > nul 2>&1 || echo answer N && goto immediatelyCopy
@echo n|comp %1 %2 > nul 2>&1 && goto loop || echo file change detected, wait %waititv% seconds && ping -w 999 -n %waititv% localhost > nul 2>&1 || echo answer N && goto immediatelyCopy
@time/t && copy/b /y %1 %2
@goto loop

:pingERR
@echo error: ping works improperly, bye~
@goto END

:exeErr
@echo error!!!!
@start "ERROR" cmd /c pause
@goto END

:argErr
@echo this is used to do copy-on-write CHECK every 30 seconds
@echo usage: %0 [source] [destination]
@echo when source change, copy to destination
@goto END

:immediatelyCopy
start "msg" cmd /c "echo n|comp %1 %2 > nul 2>&1 && echo file unchanged, not copying && pause || time/t && copy/b /y %1 %2 && pause || echo ERROR && pause"
@goto END

:remZone
@goto remZoneEnd
@rem ping is used to slow down the polling process, please make sure it works correctly
:remZoneEnd

:END
