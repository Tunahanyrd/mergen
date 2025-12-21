import subprocess
import sys


def build_app():
    """Compiles the application using Nuitka."""
    print("Starting Nuitka Build Process...")

    # Determine OS specific extension
    exe_name = "mergen"
    if sys.platform == "win32":
        exe_name += ".exe"

    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--onefile",
        "--enable-plugin=pyside6",
        "--include-data-dir=data=data",  # Include data dir if exists
        f"--output-filename={exe_name}",
        "--output-dir=build",
        "--assume-yes-for-downloads",
        "--remove-output",  # Cleanup build artifacts
        "--static-libpython=no",  # Conda fix
        "main.py",
    ]

    # Linux specific: no console for GUI?
    # For now keep console to see debug output if needed, or use --windows-disable-console on Windows
    if sys.platform == "win32":
        cmd.append("--windows-disable-console")
        cmd.append("--windows-icon-from-ico=data/mergen.ico")  # Assuming ico exists

    print(f"Running command: {' '.join(cmd)}")

    try:
        subprocess.check_call(cmd)
        print(f"Build successful! Executable is in build/{exe_name}")
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error code {e.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    build_app()
