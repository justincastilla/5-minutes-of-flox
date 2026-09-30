# 5 Minutes of Flox

One [Flox](https://github.com/flox/flox) manifest that defines an agent's whole stack: PostgreSQL, Redis, Python, uv, and a small Claude agent harness. No global installs, no docker-compose.

The agent's only tool is a shell whose `PATH` is the Flox environment's `bin/`. It can use what the manifest pins and nothing else.

## Quick start

Requires [Flox](https://flox.dev/download) and an Anthropic API key.

```bash
git clone git@github.com:justincastilla/5-minutes-of-flox.git
cd 5-minutes-of-flox
flox activate            # starts Postgres + Redis, seeds the DB, syncs Python deps
python harness.py --check
```

Run the agent:

```bash
export ANTHROPIC_API_KEY=...
python harness.py "Which customers have open high-priority tickets?"
```

## What's here

| File | Purpose |
|---|---|
| `.flox/env/manifest.toml` | Packages, env vars, activation hook, services |
| `.flox/env/manifest.lock` | Exact pins (nixpkgs revision + store paths) |
| `harness.py` | Claude agent with one PATH-scoped `run_shell` tool |
| `seed.sql` | Sample `tickets` table |
| `pyproject.toml` / `uv.lock` | Python app dependencies, managed by uv |
| `DEMO.md` | Step-by-step script for the 5-minute live demo |

## Notes

- Postgres listens on a Unix socket at `/tmp/fivemin-postgres` (no TCP). Redis listens on `127.0.0.1:6380`.
- Services auto-start on `flox activate` and stop when the last activation exits.
- Reset the database with `rm -rf .flox/cache/postgres`. The next activation re-seeds it.
- Postgres uses `trust` auth. Local development only.
