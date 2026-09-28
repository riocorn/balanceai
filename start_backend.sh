#!/bin/bash
cd /home/abhay/Downloads/medical/balanceai/src/api
exec /home/abhay/Downloads/medical/balanceai/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
