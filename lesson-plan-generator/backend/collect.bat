@echo off
xcopy /E /Y /I static\css staticfiles\css\
xcopy /E /Y /I static\js staticfiles\js\
xcopy /E /Y /I static\icons staticfiles\icons\
xcopy /E /Y /I static\images staticfiles\images\
copy /Y static\manifest.json staticfiles\
copy /Y static\sw.js staticfiles\
echo Done! Static files copied.