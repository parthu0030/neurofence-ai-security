# NeuroFence AI Security

## Project Overview

NeuroFence AI Security is an offline desktop application designed to support future analysis of large language models before deployment. The long-term goal is to help security teams identify suspicious behavior, hidden backdoors, abnormal activations, and unsafe responses in a controlled local environment.

This repository currently contains the Day 1 project foundation only. Core security analysis features are intentionally not implemented yet.

## Features Planned

- Offline-first desktop user interface
- Model and scan workflow management
- AI safety and behavior analysis modules
- Security reporting and export capabilities
- Local data persistence with SQLite and SQLAlchemy
- Rich visualizations for investigation workflows
- Structured logging and audit-friendly design

## Tech Stack

- Python 3.12
- PyQt6
- PyTorch, for future ML-based analysis
- Hugging Face Transformers, for future model integration
- SQLite
- SQLAlchemy
- Matplotlib
- ReportLab
- NumPy
- Pandas
- tqdm
- rich

## Folder Structure

```text
NeuroFence/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── assets/
│   ├── icons/
│   └── images/
├── config/
│   └── settings.py
├── models/
├── uploads/
├── scanner/
├── ui/
├── database/
├── reports/
├── logs/
├── utils/
└── tests/
```

## Installation Instructions

1. Create and activate a Python 3.12 virtual environment.
2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the desktop shell:
   ```bash
   python app.py
   ```

## Current Development Status

- Day 1 foundation completed
- Desktop shell launches with a dark theme
- Project structure initialized for future modules
- AI scanning, fuzzing, activation tracking, database workflows, reporting, and risk analysis are not yet implemented

## Notes

This project is being built in stages to keep the architecture clean, testable, and production-ready as features are added over time.
