# Scheduling the Pipeline with Cron

This runs the ETL pipeline automatically once a day.

## 1. Find your Python and project paths

```bash
which python3
# e.g. /usr/bin/python3

pwd   # while inside crypto_etl_pipeline/
# e.g. /home/youruser/crypto_etl_pipeline
```

## 2. Create a wrapper shell script

This keeps environment variables and working directory consistent for cron
(cron runs with a minimal environment, unlike your interactive shell).

Create `run_pipeline.sh` in the project root:

```bash
#!/bin/bash
cd /home/youruser/crypto_etl_pipeline
source venv/bin/activate   # if using a virtualenv
python3 -m src.pipeline >> logs/cron.log 2>&1
```

Make it executable:

```bash
chmod +x run_pipeline.sh
```

## 3. Add the cron job

Open your crontab:

```bash
crontab -e
```

Add this line to run daily at 2:00 AM:

```
0 2 * * * /home/youruser/crypto_etl_pipeline/run_pipeline.sh
```

Schedule reference:
```
minute hour day month weekday   command
0      2    *   *     *         run every day at 02:00
0      */6  *   *     *         run every 6 hours
0      2    *   *     1-5       run at 02:00, weekdays only
```

## 4. Verify it's scheduled

```bash
crontab -l
```

## 5. Check logs after it runs

```bash
tail -f logs/pipeline.log
tail -f logs/cron.log
```

If the job doesn't seem to run, the most common cause is cron using a
different PATH than your terminal — always use absolute paths in the
wrapper script (as above), and confirm the DB is reachable from cron's
non-interactive shell.
