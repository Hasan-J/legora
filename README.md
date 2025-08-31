# Kedra WorkplaceRelations Project  

Scrape documents and metadata from the [Workplace Relations](https://workplacerelations.ie/en/search) website.  
This project includes downloading documents into object storage, extracting essential metadata, and transforming them into a structured form for further use.  

---

## 🚀 Highlights  

### 📥 `extract_decisions` (Dagster Asset)  
- 🕷 **Uses Scrapy** to fetch documents and metadata from Workplace Relations  
- 📦 **Stores scrape results** in **MongoDB** (`workplacerelations.raw_decisions`) using Scrapy pipelines  
- 📑 **Manages file downloads** via Scrapy `FilesPipeline`  
- 🗄 **Stores downloaded files** in **MinIO** (`s3://legora/workplacerelations/landing_zone/full/`)  

---

### 🔄 `transform_decisions` (Dagster Asset)  
- 📤 Reads raw documents from **MongoDB** (`workplacerelations.raw_decisions`)  
- 🧹 Applies transformations (HTML content extraction, renaming files, hashing, etc.)  
- 📂 Stores transformed files in **MinIO** (`s3://legora/workplacerelations/processed/`)  
- 🗃 Inserts metadata into a **new MongoDB collection** (`workplacerelations.transformed_decisions`)  

---

⚡ Dagster Assets are configured with **monthly partitions**.  
Dagster passes the partition key (`from_date`, `to_date`) to Scrapy for time-based crawling.  

## 🛠 Getting Started  

**Prerequisites**  
- [Docker](https://docs.docker.com/get-docker/) & Docker Compose  
- Optional: [Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)  
- Optional: Python 3.12+ (if not using Dev Containers)  

**Clone the repo:**
```bash
git clone https://github.com/Hasan-J/legora.git
cd legora
```

**Copy .env.example to .env**

`.env.example` contains values that will work out-of-the-box.

```bash
cp .env.example .env
```

Now you can either follow the quick setup or manual setup below:

### Run processes and services using docker compose (Quick Setup)

```bash
docker compose up -d
```

This will start the required services:
- **MongoDB** → [http://localhost:27017](http://localhost:27017) (default creds: dev / password)
- **MinIO Console** → [http://localhost:9001](http://localhost:9001) (default creds: dev / password)
- **MinIO S3 API** → [http://localhost:9000](http://localhost:9000)
- **Dagster UI** → [http://localhost:3000](http://localhost:3000)


➡️ Open Dagster UI → Materialize Assets as needed

### Run processes and services manually (Manual Setup)

This is only needed if you want to develop or you want to manually start dagster or scrapy crawls.

**Install dependencies using [uv](https://docs.astral.sh/uv/)**

You can quickly install it using their [official documentation](https://docs.astral.sh/uv/getting-started/installation/)

```bash
uv sync
source .venv/bin/activate   # Linux
.venv\Scripts\activate      # Windows
```
<sub>💡 Alternatively, you can use `python -m venv` + `pip install -e ".[dev]"` if you prefer pip.</sub>

**Scrapy crawl**

You can run the spider with specific dates and filtering criteria:

```bash
cd src/legora_scrapy
scrapy crawl decisions -a from_date=1/8/2025 -a to_date=31/8/2025 -a body=2,1,3,15376
```

Runs the decisions Scrapy spider to crawl decisions published between 1/8/2025 and 31/8/2025, filtering results to the specified tribunals (body codes 2, 1, 3, 15376). Omitting the body argument would crawl all tribunals by default.

<sub>💡 Refer to decisions spider for code references and more info at `src/legora_scrapy/workplacerelations/spiders/decisions.py`</sub>

**Run dagster locally**

```bash
dg dev
```

Then you only need to run minio and mongodb using docker compose.

```bash
docker compose up -d mongodb minio
```

### Cleanup

Delete all containers, networks and volumes.

```bash
docker compose down -v
```
