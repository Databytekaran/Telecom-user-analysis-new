# TellCo User Analytics

Analysis of one month of aggregated xDR (data session detail record) data from **TellCo**, a mobile service provider in the Republic of Pefkakia. The goal is to find growth opportunities and give an investor a clear recommendation: **buy or sell TellCo?**

The project covers four sub-objectives, delivered as a pip-installable Python package, a web dashboard, a feature store and a written report (max. 20 slides).

> **Status:** replace the placeholders marked `<...>` (GitHub URL, screenshots, results) once the work is done. Tick the checklists at the end as you go.

---

## Table of contents
1. [Business context](#1-business-context)
2. [Objectives and tasks](#2-objectives-and-tasks)
3. [Project structure](#3-project-structure)
4. [Installation](#4-installation)
5. [Usage](#5-usage)
6. [Dashboard](#6-dashboard)
7. [Feature store](#7-feature-store)
8. [Model tracking and deployment](#8-model-tracking-and-deployment)
9. [MySQL export](#9-mysql-export)
10. [Testing and CI/CD](#10-testing-and-cicd)
11. [Docker](#11-docker)
12. [Key findings and recommendation](#12-key-findings-and-recommendation)
13. [Limitations](#13-limitations)
14. [Deliverables checklist](#14-deliverables-checklist)

---

## 1. Business context
An investor who buys undervalued assets wants a data-driven due diligence on TellCo. TellCo's owners shared financial data but never analysed their system-generated data. This project analyses customer behaviour on the network (Social Media, Google, Email, YouTube, Netflix, Gaming and Other apps) to answer:

* Who are the customers and which handsets do they use?
* How engaged are they, and where should network resources go?
* How good is their network experience (TCP retransmission, RTT, throughput, handset)?
* How satisfied are they, and can satisfaction be predicted?

## 2. Objectives and tasks

| Task | Focus | What is produced |
|---|---|---|
| **1. User Overview** | Handsets and application usage | Top 10 handsets, top 3 manufacturers, top 5 handsets per manufacturer; per-user aggregates (sessions, duration, DL/UL, volume per app); EDA (descriptive statistics, dispersion, univariate/bivariate plots, deciles by duration, correlation matrix, PCA) |
| **2. User Engagement** | Sessions frequency, duration, total traffic | Top 10 customers per metric; normalisation + k-means (k=3); cluster min/max/mean/total; top 10 users per app; top 3 apps chart; elbow method for the best k |
| **3. Experience Analytics** | TCP retransmission, RTT, throughput, handset type | Per-customer aggregates; top/bottom/most frequent 10 values per metric; throughput and retransmission per handset; k-means (k=3) experience clusters with descriptions |
| **4. Satisfaction Analysis** | Engagement score + experience score | Engagement score (distance to least-engaged cluster); experience score (distance to worst-experience cluster); satisfaction = average of both; top 10 satisfied customers; regression model; k-means (k=2); per-cluster averages; MySQL export; model tracking |

**Data treatment rule (Tasks 1-3):** missing values and outliers are replaced with the **mean** (numeric columns) or the **mode** (categorical columns such as handset type) of the corresponding column.

## 3. Project structure
Proposed layout - adapt it to what you actually build.

```
telco-user-analytics/
├── .github/workflows/ci.yml        # CI: lint, tests, coverage, Docker build
├── data/
│   ├── raw/                        # original xDR file (git-ignored)
│   └── processed/                  # cleaned data (git-ignored)
├── feature_store/                  # saved feature tables + metadata
├── notebooks/                      # EDA and experiments
├── dashboard/
│   └── app.py                      # Streamlit app (multi-page)
├── src/telco_analytics/
│   ├── __init__.py
│   ├── data_loading.py             # read raw data
│   ├── cleaning.py                 # missing values / outliers (mean / mode)
│   ├── overview.py                 # Task 1
│   ├── engagement.py               # Task 2
│   ├── experience.py               # Task 3
│   ├── satisfaction.py             # Task 4 (scores, regression, k-means)
│   ├── feature_store.py            # save / load features
│   ├── db.py                       # MySQL export
│   └── tracking.py                 # model run tracking
├── tests/                          # pytest unit tests
├── reports/                        # slides (<= 20), figures, screenshots
├── Dockerfile
├── requirements.txt
├── setup.py  (or pyproject.toml)
├── .gitignore
└── README.md
```

## 4. Installation

Requirements: Python 3.9+, (optional) Docker, (optional) MySQL 8.

```bash
git clone <your-github-url>.git
cd telco-user-analytics

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
pip install -e .                   # install the package (editable)
```

Place the xDR data file in `data/raw/` (the dataset and the column descriptions are linked in the assignment brief: `<data link>`).

## 5. Usage

```python
from telco_analytics import cleaning, overview, engagement, experience, satisfaction

df = cleaning.load_and_clean("data/raw/<xdr_file>")   # mean/mode treatment
user_agg = overview.aggregate_per_user(df)             # Task 1.1
eng = engagement.run(df)                               # Task 2
exp = experience.run(df)                               # Task 3
scores = satisfaction.compute_scores(eng, exp)         # Task 4
```

> The function names above are examples - keep them in sync with your real API.

Typical workflow:

| Step | Command |
|---|---|
| Run the full analysis | `python -m telco_analytics.run_all` |
| Start the dashboard | `streamlit run dashboard/app.py` |
| Run the tests | `pytest --cov=telco_analytics` |

## 6. Dashboard
A web dashboard (Streamlit) with one page per task, so the findings can be explored in any remote browser:

* **User Overview** - top handsets and manufacturers, application usage
* **User Engagement** - top users, engagement clusters, elbow plot
* **Experience** - throughput / TCP retransmission per handset, experience clusters
* **Satisfaction** - scores, top satisfied customers, cluster summary

```bash
streamlit run dashboard/app.py
```

Screenshot: `<reports/dashboard_screenshot.png>`
Live link (if deployed): `<url>`

## 7. Feature store
A small reusable store for selected features (for example per-user engagement and experience metrics) so they can be reused on similar problems.

* Features are saved as versioned tables (Parquet/CSV) in `feature_store/` together with a metadata file (name, description, source columns, creation date).
* Load them with `telco_analytics.feature_store.load("<feature_set_name>")`.

## 8. Model tracking and deployment
**Mandatory (Task 4.7):** the satisfaction model is deployed and tracked. Each run records:

* code version (git commit hash)
* start and end time
* source (data/file used)
* parameters
* metrics (including loss convergence)
* artifacts (model file, CSV outputs, screenshots)

Tool: `<MLflow / other>`. Run the tracking UI with:

```bash
mlflow ui          # if MLflow is used
```

Tracking report and screenshots: `<reports/model_tracking/>`

## 9. MySQL export
The final table (user ID, engagement score, experience score, satisfaction score) is exported to a local MySQL database.

```bash
# set your own credentials; do not commit them
export MYSQL_USER=<user>
export MYSQL_PASSWORD=<password>
export MYSQL_HOST=localhost
export MYSQL_DB=<database>
python -m telco_analytics.db
```

Screenshot of the `SELECT` query output: `<reports/mysql_select.png>`

## 10. Testing and CI/CD
* **Unit tests:** `pytest`, with coverage reported by `pytest --cov=telco_analytics`. Aim for good coverage of cleaning, aggregation, scoring and the feature store.
* **CI/CD:** GitHub Actions workflow in `.github/workflows/ci.yml` that installs the package, runs linting and tests with coverage, and builds the Docker image on every push and pull request.

Minimal workflow example:

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt && pip install -e . pytest pytest-cov
      - run: pytest --cov=telco_analytics
      - run: docker build -t telco-analytics .
```

## 11. Docker
```bash
docker build -t telco-analytics .
docker run -p 8501:8501 telco-analytics        # dashboard on http://localhost:8501
```

## 12. Key findings and recommendation
Fill this section from your real results; do not publish numbers you have not computed.

* **Overview:** `<top handsets / manufacturers, app usage>`
* **Engagement:** `<cluster sizes, most used apps, best k>`
* **Experience:** `<throughput and retransmission by handset, cluster descriptions>`
* **Satisfaction:** `<score distribution, regression performance, clusters>`
* **Growth potential:** `<positive / negative, with data and graphs>`
* **Recommendation:** `<buy / do not buy TellCo and why>`

The full argument is in the slides: `<reports/slides.pdf>` (max. 20 slides including title page and references).

## 13. Limitations
Describe the limits of your analysis, for example:

* only **one month** of data, so seasonality and trends cannot be assessed;
* no revenue or cost data in the xDR file, so profitability is inferred from usage;
* replacing outliers and missing values with the mean/mode reduces variance and can hide real behaviour;
* engagement, experience and satisfaction scores are constructed from distances to cluster centres, not from customer surveys;
* the dataset describes data sessions only (no voice/SMS usage).

## 14. Deliverables checklist

**Project requirements**
- [ ] Reusable code for data preparation and cleaning
- [ ] Dashboard showing the findings
- [ ] Reusable feature store
- [ ] Code installable via `pip`
- [ ] Unit tests with good coverage
- [ ] CI/CD (GitHub Actions or Travis)
- [ ] Dockerfile

**Analysis**
- [ ] Task 1 - User Overview (1.1, 1.2)
- [ ] Task 2 - User Engagement (2.1)
- [ ] Task 3 - Experience Analytics (3.1 - 3.4)
- [ ] Task 4 - Satisfaction Analysis (4.1 - 4.6)
- [ ] Task 4.7 - Model deployment tracking (mandatory)

**Final submission**
- [ ] Slides (max. 20) with recommendation, data/graphs, limitations and purchase decision
- [ ] GitHub link to the dashboard code + dashboard screenshot
- [ ] GitHub link to the data analysis code

## License
`<choose a license, e.g. MIT>`

## Acknowledgements
Project brief: Nexthikes IT Solutions - *User Analytics in the Telecommunication Industry*.
