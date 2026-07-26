@echo off
cd /d D:\Projects\crypto_etl_pipeline
call venv\Scripts\activate.bat
python -m src.pipeline >> logs\cron.log 2>&1
