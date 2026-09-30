"""Minimal agent harness: Claude + one shell tool scoped to the Flox environment.

    python harness.py --check          # show what the agent can see (no API call)
    python harness.py "your task"      # run the agent
"""

import os
import shutil
import subprocess
import sys

FLOX_ENV = os.environ.get("FLOX_ENV")
# The agent's entire toolbox: whatever the manifest put in $FLOX_ENV/bin.
AGENT_PATH = f"{FLOX_ENV}/bin" if FLOX_ENV else ""
TOOLS_TO_CHECK = ["psql", "pg_isready", "redis-cli", "python3", "uv", "curl", "git", "brew"]


def check() -> None:
    if not FLOX_ENV:
        print("✗ Not inside a Flox environment -- agent would inherit the host PATH.")
    for tool in TOOLS_TO_CHECK:
        found = shutil.which(tool, path=AGENT_PATH) if AGENT_PATH else shutil.which(tool)
        print(f"  {'✓' if found else '✗'} {tool:<10} {found or 'not available'}")
    if FLOX_ENV:
        pg = subprocess.run(["pg_isready", "-q"], env=os.environ).returncode == 0
        rd = subprocess.run(["redis-cli", "-p", os.environ["REDIS_PORT"], "ping"],
                            capture_output=True, text=True).stdout.strip() == "PONG"
        print(f"  postgres: {'up' if pg else 'down'}   redis: {'up' if rd else 'down'}")


def run_shell(command: str) -> str:
    """Run a shell command. Available CLIs: psql (Postgres, already configured via
    PG* env vars), redis-cli (use -p $REDIS_PORT), python3, uv. Nothing else is installed.

    Args:
        command: The shell command to run.
    """
    print(f"\n$ {command}")
    env = {**os.environ, "PATH": AGENT_PATH}
    result = subprocess.run(["/bin/sh", "-c", command], env=env,
                            capture_output=True, text=True, timeout=60)
    output = (result.stdout + result.stderr).strip() or f"(exit {result.returncode})"
    print(output)
    return output


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] == "--check":
        check()
        return
    if not FLOX_ENV:
        sys.exit("Run inside the Flox environment: flox activate -- python harness.py ...")

    import anthropic
    from anthropic import beta_tool

    client = anthropic.Anthropic()
    runner = client.beta.messages.tool_runner(
        model="claude-opus-5-5",
        max_tokens=16000,
        output_config={"effort": "low"},
        betas=["server-side-fallback-2026-07-01"],
        extra_body={"fallbacks": "default"},
        system="You are an ops agent. Use run_shell to inspect the Postgres database and "
               "Redis. Be brief. Finish with a short plain-text answer.",
        tools=[beta_tool(run_shell)],
        messages=[{"role": "user", "content": " ".join(sys.argv[1:])}],
    )
    for message in runner:
        if message.stop_reason == "refusal":
            sys.exit("Request was declined.")
        for block in message.content:
            if block.type == "text" and message.stop_reason == "end_turn":
                print(f"\n{block.text}")


if __name__ == "__main__":
    main()
