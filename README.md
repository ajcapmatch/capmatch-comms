# CapMatch Communications Services

This repository hosts CapMatch's outbound communications workloads (email digests today, with room for transactional email, SMS or push in the future). Each service lives under `services/<service-name>` with its own runtime configuration, Dockerfile and deployment pipeline.

## Layout

- `services/email-digest/` – daily digest job previously located in `capmatch-dev/workers/email-digest`. Contains Python source, Supabase interaction logic, Docker/Cloud Build configurations and service-specific README.
- `infra/` (optional) – add Terraform, Cloud Build triggers, or other shared infrastructure definitions here when they become available.
- `packages/` (optional) – space for shared Python packages or libraries once multiple services need to share code (e.g., Supabase helpers, templating utilities).

## Development Workflow

1. Choose the service directory you want to work on (e.g., `services/email-digest`).
2. Follow its README for environment variables, local dev instructions, and deployment steps.
3. Use uv or your preferred virtual environment manager inside each service. The repo-level `pyproject.toml` tracks workspace members so tooling can detect all services.

## Next Steps

- Add future notification services under `services/`.
- Extract shared helpers into `packages/` when duplication appears.
- Wire up CI/CD at the repo root so each service can build, test, and deploy independently.

