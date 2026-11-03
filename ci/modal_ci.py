"""Run latest Node.js LTS / npm latest Pi compatibility checks on Modal."""

import os
from pathlib import Path
import subprocess

import modal


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = "/workspace"
app = modal.App("pi-is-ephemeral-ci")


def make_image():
    image = (
        modal.Image.from_registry("node:lts-bookworm-slim", add_python="3.11")
        .env({
            "CI": "true",
            "PI_OFFLINE": "1",
            "NPM_CONFIG_REGISTRY": "https://registry.npmjs.org/",
        })
        .workdir(WORKSPACE)
    )
    # Modal re-imports this module in the container. Only the dispatcher should
    # inspect upload inputs; never upload .git, node_modules, or credentials.
    if modal.is_local():
        for path in ("package.json", "ci/modal_ci.py", "ci/test_modal_ci.py"):
            image = image.add_local_file(ROOT / path, f"{WORKSPACE}/{path}")
        for path in ("extensions", "test"):
            image = image.add_local_dir(ROOT / path, f"{WORKSPACE}/{path}")
    return image


@app.function(image=make_image(), cpu=1, memory=2048, timeout=600, retries=0)
def compatibility():
    env = {**os.environ, "PI_OFFLINE": "1"}
    for command in (
        ["python", "-m", "unittest", "discover", "-s", "ci", "-p", "test_*.py"],
        ["npm", "install", "--no-save", "--package-lock=false", "--ignore-scripts",
         "@earendil-works/pi-coding-agent@latest"],
        ["node", "--version"],
        ["npm", "ls", "@earendil-works/pi-coding-agent", "--depth=0"],
        ["node_modules/.bin/pi", "--version"],
        ["npm", "test"],
        ["npm", "run", "test:integration"],
    ):
        print(f"+ {' '.join(command)}", flush=True)
        # Propagate install/test failures to modal run and the GitHub check.
        subprocess.run(command, cwd=WORKSPACE, env=env, check=True)


@app.local_entrypoint()
def run_tests():
    """GitHub only dispatches; no Node commands run on the Actions runner."""
    compatibility.remote()
