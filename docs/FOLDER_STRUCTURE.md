# Folder Structure

```text
industrial-troubleshooting-copilot/
├── README.md
├── .env.example
├── .gitignore
├── app/
│   ├── frontend/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── public/
│   │   ├── styles/
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── backend/
│       ├── app/
│       │   ├── api/
│       │   ├── core/
│       │   ├── services/
│       │   ├── models/
│       │   └── schemas/
│       ├── main.py
│       ├── requirements.txt
│       └── pyproject.toml
├── data/
│   ├── sample-docs/
│   ├── uploads/
│   ├── processed/
│   └── chroma/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── FOLDER_STRUCTURE.md
│   ├── API_SPEC.md
│   ├── SCHEMA.md
│   └── STARTER_PLAN.md
├── infra/
│   ├── docker-compose.yml
│   └── deployment-notes.md
├── scripts/
│   ├── seed_sample_docs.sh
│   ├── run_backend.sh
│   └── run_frontend.sh
└── tests/
    ├── backend/
    └── smoke/
```
