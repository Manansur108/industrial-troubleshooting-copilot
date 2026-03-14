# Setup Guide

## Backend
```bash
cd app/backend
python3 -m venv ../../.venv-backend
source ../../.venv-backend/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend
```bash
cd app/frontend
cp .env.local.example .env.local
npm install
npm run dev
```

## Sample demo data
```bash
./scripts/seed_sample_docs.sh
```

Then upload the files from `data/sample-docs/` in the UI.
