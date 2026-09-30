# One Manifest, Whole Stack — demo runbook

Stack: Flox 1.17 · PostgreSQL 16.15 · Redis 8.10.2 · Python 3.13 · uv 0.12 · Claude Opus 5.5 (Anthropic SDK tool runner)

Files in this repo:

| File | Role |
|---|---|
| `.flox/env/manifest.toml` | The environment: packages, vars, hook, services |
| `.flox/env/manifest.lock` | Content-hash pins (nixpkgs rev + `/nix/store` paths) |
| `manifest.demo.toml` | Same manifest, kept at the root so you can `flox edit -f` it on stage |
| `seed.sql` | `tickets` table the agent queries |
| `pyproject.toml` | App deps (`anthropic`), owned by uv, not Flox |
| `harness.py` | Agent with one `run_shell` tool whose `PATH` is **only** `$FLOX_ENV/bin` |

---

## Night before (prep)

```bash
cd ~/Code/5-minutes-of-flox
export ANTHROPIC_API_KEY=...        # or: ant auth login
flox activate -- python harness.py "How many open high-priority tickets are there, and for whom?"
```

That warms the Nix store (packages, Redis 7.2.7 for the rollback) and the uv cache, so nothing downloads on venue Wi-Fi. Also warm the live-build directory once, then delete it:

```bash
mkdir -p /tmp/stage && cd /tmp/stage && flox init && flox install postgresql_16 redis python313 uv curl && cd - && rm -rf /tmp/stage
```

Terminal: large font, `clear` before each beat. Have a second terminal already `cd`'d into this repo for the "second machine" beat.

---

## Live run of show (5:00)

### 0:00–0:30 — The bare host

```bash
python3 --version          # 3.9.6 from macOS
which psql redis-cli       # not found
python3 harness.py --check # no psql/redis-cli, but curl, git, brew leak in from the host
```

Say: *an agent's capabilities are whatever is on its PATH. On my laptop that's random.*

### 0:30–2:30 — Build it from an empty directory

```bash
mkdir /tmp/stage && cd /tmp/stage
flox init
flox install postgresql_16 redis python313 uv
cp ~/Code/5-minutes-of-flox/{seed.sql,pyproject.toml,harness.py} .
flox edit -f ~/Code/5-minutes-of-flox/manifest.demo.toml
```

Then `cat .flox/env/manifest.toml` and walk the sections. This is the code walkthrough:

- `[install]` is the system layer. Four packages from Nixpkgs, nothing global.
- `[vars]` gives Postgres a unix socket in `/tmp/fivemin-postgres` (no TCP, so it can't collide with a host Postgres) and Redis on port **6380**, off the default.
- `[hook]` runs on every activation. First run only (guarded by `$PGDATA` existing): `initdb`, seed, stop. Every run: `uv sync` and source `.venv`, because **uv owns Python deps and Flox owns the system**.
- `[services]` sets `auto-start = true`, so there's no docker-compose. Postgres and Redis run from the same file as the tools.

### 2:30–3:30 — Activate; agent runs against the backend

```bash
flox activate
python harness.py --check
```

✓ psql / redis-cli / python3 / uv, ✗ curl / git / brew, `postgres: up redis: up`.

```bash
python harness.py "Which customers have open high-priority tickets? Cache the answer in Redis under key report:high."
```

Audience sees the agent's `$ psql ...` and `$ redis-cli ...` calls stream by.

Optional beat, the toolbox is the manifest:

```bash
python harness.py "Fetch https://example.com with curl"   # agent: curl: command not found
flox install curl                                           # in another shell, or exit + re-activate
```

### 3:30–4:30 — Change a version, roll it back, second machine

Back in `~/Code/5-minutes-of-flox` (it's a git repo):

```bash
flox edit            # add:  redis.version = "7.2.7"   under [install]
flox activate -- redis-server --version     # v=7.2.7
git diff --stat                             # manifest.toml +1, manifest.lock rewritten
git checkout -- .flox                       # rollback
flox activate -- redis-server --version     # v=8.10.2
```

Show what's actually pinned (the content hash, not the tag):

```bash
jq -c '.packages[] | select(.install_id=="redis" and .system=="aarch64-darwin") | {version, rev, outputs}' .flox/env/manifest.lock
```

Second machine, pick one:

- **git:** `git clone <repo> && cd <repo> && flox activate`. Same lockfile, same store paths.
- **FloxHub:** `flox push` once beforehand, then on the other box `flox activate -r <you>/5-minutes-of-flox`. This also unlocks `flox generations rollback`, which only works for pushed envs.
- **Container:** `flox containerize --runtime docker` (needs Docker running).

### 4:30–5:00 — Takeaway

1. Scope the agent to a declared environment: its toolbox becomes reviewable and versioned in the diff.
2. Keep the system layer (DBs, CLIs, compilers) separate from language deps. uv still owns `pyproject.toml`.
3. Run backing services from the same definition as the tools.
4. Pin by content hash (`manifest.lock`), not by version tag.

---

## Gotchas found while building this

- `flox install redis@7.2.7` when `redis` is already installed is a **no-op** ("already installed"). Change versions with `redis.version = "..."` in the manifest.
- `flox generations` / `rollback` only work for environments pushed to FloxHub. For a local dir, git is the rollback.
- Services stop when the last activation exits. `flox activate -- cmd` starts them (auto-start) and tears them down afterwards. Give it ~2s before the first query.
- Postgres socket paths must stay short (macOS limit is 104 bytes), so the socket lives in `/tmp/fivemin-postgres`, not `$FLOX_ENV_CACHE`.
- `auth=trust` in `initdb` is dev-only.
- Reset the DB: `rm -rf .flox/cache/postgres`. The next activation re-inits and re-seeds.
