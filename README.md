# E-Commerce Data Integration & Analytics Pipeline

An end-to-end data pipeline that collects e-commerce data from multiple sources (API and CSV), cleans and models it in a relational database, orchestrates the workflow with Airflow, validates data quality, and presents the results in an analytics dashboard.

## Architecture

```
API + CSV  ->  Python ingestion  ->  Cleaning  ->  SQL database  ->  Data quality checks  ->  Dashboard
                                                        ^
                                              Airflow orchestration
```

## Team & Responsibilities

| Member | Responsibility |
|--------|----------------|
| Member 1 - NAME | Data collection with Python: API requests and CSV files |
| Member 2 - NAME | Data cleaning, database design, and SQL |
| Member 3 - NAME | Airflow orchestration, data quality checks, documentation, and dashboard |

## Project Structure

> Update this section to match your actual folders.

```
.
├── ingestion/        # Python scripts: API + CSV collection
├── sql/              # Database schema and SQL queries
├── dags/             # Airflow DAGs
├── data_quality/     # Data quality checks
├── dashboard/        # Dashboard app
├── docs/             # Documentation
├── requirements.txt
└── README.md
```

## Tech Stack

- **Python** (requests, pandas) for ingestion and cleaning
- **SQL** for database design and analytics queries
- **Apache Airflow** for orchestration
- **Data quality checks** for validation
- **Dashboard** for visualization

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/mohab065-del/ecommerce-data-pipeline.git
cd ecommerce-data-pipeline
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root (it is excluded from Git) with your own database credentials:

```
DB_SERVER=your_server
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
```

### 4. Run the pipeline

> Replace with your actual commands.

```bash
python ingestion/main.py
```

## Data Quality

Describe the checks performed (for example: null checks, duplicate checks, valid value ranges, row counts) and where the results are reported.

## Dashboard

Describe how to launch the dashboard and what it shows (for example: sales by category, top products, trends).

## Documentation

Additional documentation is available in the `docs/` folder.

## License

For educational / academic use.
