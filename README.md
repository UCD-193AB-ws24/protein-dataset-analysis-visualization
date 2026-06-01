# LocusCGVT

**Locus Comparative Genomics Visualization Tool** — an interactive web application for visualizing genes and proteins in genomic regions and their homologous relationships across genotypes or species.

Users upload coordinate files (gene positions) and similarity matrix files (pairwise scores), and LocusCGVT generates interactive graph visualizations where genes are rendered as directional nodes and homolog relationships as similarity-scored links.

## Features

- **Interactive visualization**: D3.js-powered graph with zoom, pan, tooltips, click-to-select, and focus mode
- **Multi-genome comparison**: Compare genes across multiple genotypes displayed as horizontal genome bands
- **Multi-domain analysis**: Upload up to 3 domain-specific similarity matrices; link styles encode cross-domain consistency (reciprocal in all domains, partial, or absent)
- **Adjustable similarity threshold**: Dynamically filter links by similarity score cutoff
- **Project management**: Save and reload projects with cloud storage (requires login)
- **Report export**: Download visualization summaries as Markdown, HTML, or CSV

## Quick Start

### Docker (recommended)

```bash
cd Part2
docker-compose up
```

This starts the full stack:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:3050
- **PostgreSQL**: localhost:5432

### Manual Setup

**Backend:**
```bash
cd Part2/Part2_Backend
pip install -r requirements.txt
flask --app server.py run --host=0.0.0.0 --port=3050 --debug
```

**Frontend:**
```bash
cd Part2/Part2_Frontend
npm install
npm run dev
```

## Input File Formats

### Coordinate File (CSV or Excel)

Defines gene positions within genomes.

| Column | Description |
|--------|-------------|
| `name` | Unique gene identifier |
| `protein_name` | Display name for the gene/protein |
| `genome` | Genome or genotype name |
| `position` | Ordinal position within the genome |
| `orientation` | Strand direction (`plus` or `negative`) |

For domain-specific mode, additional columns are required:
- `gene_type` — classification label (e.g., `NL`, `TNL`)
- `domain1_NAME`, `domain2_NAME`, ... — `yes`/empty indicating domain presence

### Similarity Matrix File (CSV or Excel)

A symmetric matrix of pairwise similarity scores (0–100) between genes. Row and column headers are gene identifiers matching the coordinate file's `name` column.

See [`examples/`](examples/) for sample input files.

## Example Data

The `examples/` directory contains small datasets from *Lactuca sativa* (lettuce) genotypes:

- **`examples/general/`** — Single-matrix comparison of two genotypes (CobhamGreen, GreenTowers)
- **`examples/domain/`** — Multi-domain comparison with NBS and LRR domain matrices across two genotypes (Salinas, Dandie)

To try them: open the app, click "Visualize", upload the coordinate file and matrix file(s) from either directory.

## Architecture

```
Part2/
  Part2_Backend/       Flask API (Python 3.9)
    server.py          Entry point
    controllers/       Route handlers (graph, group, auth)
    core/              Data processing (coordinate/matrix file parsing)
    parsing/           Graph generation (single-genome and multi-domain)
    database/          SQLAlchemy models and CRUD
    services/          AWS S3 integration
  Part2_Frontend/      SvelteKit app (TypeScript)
    src/routes/        Pages (landing, diagram, dashboard, help, about)
    src/lib/components/ Chart.svelte (D3), UploadModal, Navbar, ReportDownloadButton
    src/lib/           Auth, stores, UnionFind utility
  init-db/             PostgreSQL schema
Part1/                 Standalone data preparation scripts
examples/              Sample input files
```

## Data Flow

1. User uploads coordinate CSV/Excel + similarity matrix CSV/Excel
2. Backend validates, cleans, and parses files via pandas
3. Graph JSON is generated (nodes = genes with position/direction/genome, links = homolog pairs with similarity scores)
4. Frontend renders an interactive D3.js visualization
5. Optionally, users save projects (files to S3, metadata to PostgreSQL)

## Tests

```bash
# Data preparation scripts
cd Part1/simplify_headers_script && pytest test_simplify_headers.py
cd Part1/combine_coords_script && pytest test_combine_coords.py

# Backend parsing
cd Part2/Part2_Backend/parsing_testing && python test_parse.py
```

## Deployment

- **Backend**: AWS Lambda via Zappa + API Gateway
- **Frontend**: AWS S3 + CloudFront (static SPA)
- **Auth**: AWS Cognito (OIDC)
- **Database**: PostgreSQL (RDS)

## License

[MIT](LICENSE)
