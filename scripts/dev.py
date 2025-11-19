#!/usr/bin/env python3
"""
Cross-platform development launcher for SiteInsite.

This script detects the host OS, prepares a project-local Python virtual
environment, installs backend dependencies, ensures frontend packages are
installed, and starts both the FastAPI backend and the React frontend.
"""

from __future__ import annotations

import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
VENV_DIR = ROOT_DIR / ".venv"


class ProcessManager:
    def __init__(self) -> None:
        self._procs: List[subprocess.Popen] = []

    def add(self, proc: subprocess.Popen) -> None:
        self._procs.append(proc)

    def terminate_all(self, *, kill_after: float = 5.0) -> None:
        for proc in self._procs:
            if proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass

        for proc in self._procs:
            if proc.poll() is None:
                try:
                    proc.wait(timeout=kill_after)
                except subprocess.TimeoutExpired:
                    try:
                        proc.kill()
                    except Exception:
                        pass


def log(message: str) -> None:
    print(f"[dev] {message}")


def detect_platform() -> str:
    system = platform.system()
    log(f"Detected platform: {system or 'Unknown'}")
    return system


def ensure_virtualenv(system: str) -> Path:
    if not VENV_DIR.exists():
        log(f"Creating virtual environment at {VENV_DIR}...")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)

    python_executable = (
        VENV_DIR / "Scripts" / "python.exe"
        if system == "Windows"
        else VENV_DIR / "bin" / "python"
    )

    if not python_executable.exists():
        raise RuntimeError(
            f"Expected virtualenv python at {python_executable}, "
            "but it was not found."
        )

    return python_executable


def ensure_backend_dependencies(venv_python: Path) -> None:
    log("Upgrading pip and wheel inside virtualenv...")
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "--upgrade", "pip", "wheel"],
        check=True,
    )

    requirements_file = BACKEND_DIR / "requirements.txt"
    log(f"Installing backend dependencies from {requirements_file}...")
    subprocess.run(
        [str(venv_python), "-m", "pip", "install", "-r", str(requirements_file)],
        check=True,
    )


def ensure_frontend_dependencies() -> None:
    log("Ensuring frontend dependencies are installed (npm install)...")
    subprocess.run(["npm", "install"], cwd=FRONTEND_DIR, check=True)


def start_backend(venv_python: Path) -> subprocess.Popen:
    env = os.environ.copy()
    if platform.system() == "Windows":
        venv_bin = VENV_DIR / "Scripts"
    else:
        venv_bin = VENV_DIR / "bin"

    env["VIRTUAL_ENV"] = str(VENV_DIR)
    env["PATH"] = str(venv_bin) + os.pathsep + env.get("PATH", "")

    log("Starting FastAPI backend on http://localhost:5051...")
    return subprocess.Popen(
        [str(venv_python), "-m", "uvicorn", "backend.app:app", "--reload", "--port", "5051"],
        cwd=ROOT_DIR,
        env=env,
    )


def start_frontend() -> subprocess.Popen:
    log("Starting React frontend on http://localhost:5173...")
    return subprocess.Popen(["npm", "run", "dev"], cwd=FRONTEND_DIR)


def check_prerequisites() -> None:
    if shutil_which("npm") is None:
        raise RuntimeError(
            "npm was not found on your PATH. Please install Node.js 18+ before continuing."
        )

    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10 or newer is required to run the development server.")


def shutil_which(command: str) -> Optional[str]:
    from shutil import which

    return which(command)


def main() -> int:
    try:
        check_prerequisites()
    except RuntimeError as exc:
        log(str(exc))
        return 1

    system = detect_platform()

    try:
        venv_python = ensure_virtualenv(system)
        ensure_backend_dependencies(venv_python)
        ensure_frontend_dependencies()
    except subprocess.CalledProcessError as exc:
        log(f"Command failed with exit code {exc.returncode}: {' '.join(exc.cmd)}")
        return exc.returncode or 1
    except RuntimeError as exc:
        log(str(exc))
        return 1

    manager = ProcessManager()

    def handle_exit(signum, frame):  # type: ignore[no-untyped-def]
        log(f"Received signal {signum}, shutting down services...")
        manager.terminate_all()
        sys.exit(0)

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, handle_exit)

    try:
        backend_proc = start_backend(venv_python)
        manager.add(backend_proc)

        frontend_proc = start_frontend()
        manager.add(frontend_proc)

        log("Services are starting...")
        log("Backend API: http://localhost:5051")
        log("Frontend UI: http://localhost:5173")
        log("API Docs: http://localhost:5051/docs")

        # Wait for processes; return when one of them exits.
        exit_code = 0
        while True:
            if backend_proc.poll() is not None:
                exit_code = backend_proc.returncode or 0
                log("Backend process exited.")
                break
            if frontend_proc.poll() is not None:
                exit_code = frontend_proc.returncode or 0
                log("Frontend process exited.")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        log("Keyboard interrupt received, stopping services...")
        exit_code = 0
    finally:
        manager.terminate_all()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())

