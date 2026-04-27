# Northstar People Intelligence

Northstar is a portfolio-ready employee attrition intelligence workspace built from the original notebook analysis in this repository. It turns a small employee dataset into a deployable product surface: reusable Python modules, a browser dashboard, scenario scoring, and deployment assets.

## Why this project works in a portfolio

- it starts from real exploratory cleaning work rather than skipping straight to a polished UI
- it presents the analysis as an enterprise-facing product instead of a notebook dump
- it shows end-to-end ownership: data prep, model logic, UI, API surface, testing, and deployment packaging

## Product surface

- executive attrition dashboard with department risk concentration
- scenario scoring form for employee-level retention review
- ranked roster of high-risk employees with driver explanations
- reusable service layer for analytics and prediction
- Docker deployment configuration

## Technical approach

This repo intentionally keeps the stack compact:

- Python standard-library web server for easy deployment
- pandas and numpy for data handling and model math
- a custom logistic regression implementation so the project does not depend on a heavier ML serving stack for a small demo dataset
- static HTML, CSS, and JavaScript for a controlled, non-generic enterprise UI

## Repository structure

```text
Employee_ml/
|-- data/
|   |-- processed/
|   `-- raw/
|-- src/employee_ml/
|   |-- data.py
|   |-- model.py
|   `-- service.py
|-- tests/
|   `-- test_service.py
|-- web/
|   |-- app.js
|   |-- index.html
|   `-- styles.css
|-- server.py
|-- Dockerfile
`-- render.yaml
```

## Local run

Create an environment, install dependencies, then start the server:

```bash
pip install -r requirements.txt
python server.py
```

The app will be available at `http://127.0.0.1:8000`.

## Test

```bash
python -m unittest discover -s tests
```

## API

- `GET /api/health`
- `GET /api/dashboard`
- `POST /api/predict`

Example payload for `POST /api/predict`:

```json
{
  "age": 31.0,
  "salary": 58000,
  "department": "Engineering",
  "tenure_years": 1.6,
  "performance_score": 2,
  "perf_was_missing": 0
}
```

## Deployment

### Docker

```bash
docker build -t northstar-people-intelligence .
docker run -p 8000:8000 northstar-people-intelligence
```

### Render

`render.yaml` is included for a simple Docker-based deploy.

## Notes

- dataset: `272` cleaned employee records
- this is a portfolio demo, not an HR production model
- the original notebook remains in the repo as source analysis context
