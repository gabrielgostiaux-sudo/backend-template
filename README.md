# my-project-template

A Python project template using the layered structure from [Cosmic Python](https://github.com/cosmicpython/code/tree/appendix_project_structure).

## Project structure

```text
src/my_project_template/
├── adapters/       # implementations of ports and external integrations
├── domain/         # domain model and business rules
├── entrypoints/    # driving adapters such as CLI or web handlers
├── service_layer/  # use cases and application orchestration
└── config.py       # application configuration
tests/
├── unit/
├── integration/
└── e2e/
```

The package areas follow the Cosmic Python example project. Add modules to the
appropriate layer as the application grows; keep business rules in `domain`
independent of infrastructure in `adapters`.

## Development

Requires [uv](https://docs.astral.sh/uv/) and Git. Python 3.12 or newer is
managed by uv according to `pyproject.toml`.

```sh
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run ty check
```

## Docker

Build the Python image and run Python in the container:

```sh
docker compose build app
docker compose run --rm --no-deps app python --version
```

Start PostgreSQL with Compose and open a Python session:

```sh
docker compose up -d db
docker compose run --rm app
```

The app container receives `DATABASE_URL` and waits for the Compose database to
be healthy. Configure `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and
`POSTGRES_PORT` with environment variables or a local `.env` file. The default
credentials are for local development only.

## Terraform

`terraform/` uses the local Docker provider, following the Colima setup in the
Terraform training project. It builds this project's Python image and creates
a PostgreSQL container, Docker network, and persistent volume. It defaults to
Colima's `~/.colima/default/docker.sock`; start Colima with
`colima start --runtime docker` before applying. Override the socket with the
`docker_host` variable if needed.

Terraform is an alternative to the Compose services; do not run both at once
with the default container names and PostgreSQL port.

```sh
cd terraform
terraform init
terraform plan
terraform apply
terraform output
terraform destroy
```

Override PostgreSQL defaults with `-var` or a `*.tfvars` file. Terraform state
can contain database credentials; keep state files private and never commit
them.

The `prek` hooks run Python and Terraform formatting/lint checks before commit.
On push, they also run Python type/tests, Terraform validation/TFLint, and
Docker Compose validation. Install `uv`, `terraform`, `tflint`, Docker with
Compose, and start Colima (or another Docker daemon) before installing/running
the hooks. Initialize the Terraform working directory once before the first
push:

```sh
cd terraform && terraform init -backend=false && cd ..
uv tool install prek
prek install
prek run --all-files
prek run --all-files --hook-stage pre-push
```

CI runs the same pre-commit and pre-push hooks on pushes to `main` and pull
requests. `uv.lock` is committed to keep dependency versions reproducible.

## License

Add your license here.
