set PYTHON_ROOT_PATH=C:\Users\ddtkh\AppData\Local\Programs\Python\Python36
set WORKING_DIR=C:\Users\ddtkh\Desktop\qc_scale

rem generate GUIs
%PYTHON_ROOT_PATH%\Scripts\pyuic5.exe -x %WORKING_DIR%\qc_scale_gui.ui -o %WORKING_DIR%\qc_scale_gui.py
%PYTHON_ROOT_PATH%\Scripts\pyuic5.exe -x %WORKING_DIR%\com_config_gui.ui -o %WORKING_DIR%\com_config_gui.py

rem run application
%PYTHON_ROOT_PATH%\python.exe %WORKING_DIR%\main.py