#!/bin/bash
# Azure App Service startup script
echo "Starting Thota Mitra Web Service..."
python -m app.db.init_db
uvicorn app.main:app --host 0.0.0.0 --port 8000
