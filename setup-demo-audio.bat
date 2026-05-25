@echo off
REM setup-demo-audio.bat
REM Creates folder structure for demo audio testing on Windows

echo Creating demo audio structure...
echo.

REM Create main directory
if not exist "frontend\public\audio\ragas" mkdir "frontend\public\audio\ragas"

REM Create band subdirectories
for %%B in (T1 T2 A1 A2 B1 B2) do (
  if not exist "frontend\public\audio\ragas\%%B" mkdir "frontend\public\audio\ragas\%%B"
)

echo Folder structure created!
echo.

REM Define ragas using temporary batch variables
setlocal enabledelayedexpansion

set "T1=Ahir_Bhairav Madhmad_Sarang Malkauns"
set "T2=Todi Bhimpalasi Darbari_Kanada"
set "A1=Bhairav Shuddh_Sarang Yaman"
set "A2=Alhaiya_Bilawal Multani Bhopali"
set "B1=Jaunpuri Kafi Khamaj"
set "B2=Hindol Marwa Shankara"

REM Create dummy MP3 files
echo Note: Creating minimal MP3 files for testing...
echo This includes a Python script to create proper audio files

REM Create Python script to generate audio
(
echo import os
echo import struct
echo.
echo def create_silent_mp3(filepath, duration=10^):
echo     """Create a minimal valid MP3 file with ~duration seconds of silence"""
echo     os.makedirs(os.path.dirname(filepath^), exist_ok=True^)
echo     
echo     # Minimal MP3 header for MPEG2 Layer 3
echo     # Frame length = 417 bytes at 22.05 kHz
echo     mp3_frame = b'\xff\xfb' + bytes(415^)
echo     
echo     with open(filepath, 'wb'^) as f:
echo         for _ in range(duration * 100^):
echo             f.write(mp3_frame^)
echo.
echo bands = ['T1', 'T2', 'A1', 'A2', 'B1', 'B2']
echo ragas_by_band = {
echo     'T1': ['Ahir_Bhairav', 'Madhmad_Sarang', 'Malkauns'],
echo     'T2': ['Todi', 'Bhimpalasi', 'Darbari_Kanada'],
echo     'A1': ['Bhairav', 'Shuddh_Sarang', 'Yaman'],
echo     'A2': ['Alhaiya_Bilawal', 'Multani', 'Bhopali'],
echo     'B1': ['Jaunpuri', 'Kafi', 'Khamaj'],
echo     'B2': ['Hindol', 'Marwa', 'Shankara']
echo }
echo.
echo for band in bands:
echo     for raga in ragas_by_band[band]:
echo         filepath = f'frontend\public\audio\ragas\{band}\{raga}.mp3'
echo         create_silent_mp3(filepath, duration=10^)
echo         print(f'Created: {filepath}'^)
echo.
echo print(f'\Total: {len(bands^) * sum(len(r^) for r in ragas_by_band.values(^))} files created'^)
) > create_audio.py

echo.
echo Running Python to generate audio files...
python create_audio.py

echo.
echo Done! Demo audio files created.
echo All files are minimal silent MP3s for UI testing.
echo.
echo To add real ragas:
echo 1. Download or record raga MP3 files
echo 2. Place them in frontend\public\audio\ragas\{BAND}\ folders
echo 3. Name format: {RagaName}.mp3 (e.g., Bhairav.mp3)
echo.
echo For more info, see IMPLEMENTATION_SUMMARY.md
