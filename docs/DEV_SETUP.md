# Developer setup (local)

This document describes quick commands to prepare a development environment for the demo on Windows and Unix (WSL/Git Bash).

PowerShell (Windows)

```powershell
# from repo root
cd D:\PROJECTS-REPOS\AGENT-QA
# create venv and install backend deps, run tests
infra\dev_setup.ps1
```

Bash (Linux / WSL / Git Bash)

```bash
# from repo root
cd /path/to/AGENT-QA
bash infra/dev_setup.sh
```

Run the smoke test (Windows PowerShell)

```powershell
# runs core containers and posts a demo job
infraun_smoke.ps1
```

Notes

- The CI workflow now invokes `infra/dev_setup.sh` as part of the `build-and-test` job.
- If you do not have Docker Desktop running on Windows, start it first.
- For WSL users, use the Bash script and ensure Docker is available in WSL.
