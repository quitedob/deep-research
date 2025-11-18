for /d /r %%i in (__pycache__) do if exist "%%i" rmdir /s /q "%%i"
