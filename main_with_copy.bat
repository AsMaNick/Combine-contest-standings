set Season=2025
set Stage=1
xcopy /y data\%Season%_%Stage%\settings.py settings.py
python main.py
xcopy /y created_tables\standings.html ..\acmallukrainian\%Season%\%Stage%\
TIMEOUT /T -1