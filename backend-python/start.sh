#!/usr/bin/env bash
set -euo pipefail
uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload
Thought for 14s
