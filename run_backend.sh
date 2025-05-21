#!/bin/bash
source .venv/bin/activate
uvicorn app.api.main:app --host 0.0.0.0 --port 13000 --reload --log-level debug