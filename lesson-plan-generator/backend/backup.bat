@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM  backup.bat — Django + Supabase backup for Windows
REM  Save to: D:\Lesson Project\lesson-plan-generator\backend\
REM  Run: double-click OR type "backup.bat" in CMD from backend\
REM ============================================================

REM ── Date/time stamp ──
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set DT=%%I
set DATE=%DT:~0,8%_%DT:~8,6%
set BACKUP_DIR=backups\%DATE%

echo.
echo ============================================================
echo   CBC Lesson Plan Generator — Database Backup
echo   Timestamp: %DATE%
echo ============================================================
echo.

REM ── Create backup folder ──
if not exist backups mkdir backups
mkdir %BACKUP_DIR%

REM ── Load .env.local for SUPABASE settings ──
echo Loading environment...
if exist .env.local (
    for /f "usebackq tokens=1,* delims==" %%A in (".env.local") do (
        set line=%%A
        if not "!line:~0,1!"=="#" (
            set %%A=%%B
        )
    )
    echo Found .env.local
) else if exist .env (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        set line=%%A
        if not "!line:~0,1!"=="#" (
            set %%A=%%B
        )
    )
    echo Found .env
) else (
    echo WARNING: No .env.local or .env file found
    echo Make sure SUPABASE_DATABASE_URL is set manually
)

REM ── Test DB connection ──
echo.
echo Checking database connection...
python -c "import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cbc_backend.settings'); django.setup(); from django.db import connection; connection.ensure_connection(); print('Connected to:', connection.settings_dict['HOST'])"
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Database connection failed!
    echo Check SUPABASE_DATABASE_URL in your .env.local file
    echo.
    pause
    exit /b 1
)

echo.

REM ── 1. Users and Activity ──
echo [1/3] Backing up users and activity...
python manage.py dumpdata ^
  auth.User ^
  lessons.UserProfile ^
  lessons.Subscription ^
  lessons.ManualPaymentProof ^
  lessons.GeneratedLessonPlan ^
  lessons.ChatHistory ^
  lessons.Interaction ^
  --indent 2 ^
  --output %BACKUP_DIR%\users_and_data.json

if %errorlevel% neq 0 (
    echo ERROR: Failed to backup users data
    pause
    exit /b 1
)
echo Done: users_and_data.json

REM ── 2. Curriculum ──
echo.
echo [2/3] Backing up curriculum...
python manage.py dumpdata ^
  lessons.Level ^
  lessons.Class ^
  lessons.Subject ^
  lessons.Unit ^
  lessons.Lesson ^
  lessons.TeachingStrategy ^
  lessons.LessonStrategyStep ^
  --indent 2 ^
  --output %BACKUP_DIR%\curriculum.json

if %errorlevel% neq 0 (
    echo ERROR: Failed to backup curriculum data
    pause
    exit /b 1
)
echo Done: curriculum.json

REM ── 3. Config ──
echo.
echo [3/3] Backing up config and banners...
python manage.py dumpdata ^
  lessons.BotConfig ^
  lessons.BotResponse ^
  lessons.QuickReply ^
  lessons.TopBanner ^
  lessons.HeroBanner ^
  lessons.BottomAd ^
  --indent 2 ^
  --output %BACKUP_DIR%\config.json

if %errorlevel% neq 0 (
    echo ERROR: Failed to backup config data
    pause
    exit /b 1
)
echo Done: config.json

REM ── Summary ──
echo.
echo ============================================================
echo   Backup Complete!
echo   Location: %BACKUP_DIR%\
echo ============================================================
echo.
dir %BACKUP_DIR%
echo.
echo Press any key to close...
pause >nul