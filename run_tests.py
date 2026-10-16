"""Cross-platform test runner that avoids the Windows pytest.exe wrapper.

Python 3.14 on this Windows host cannot create an asyncio event loop; use the
project's compatible Python 3.12 interpreter/venv when invoking this runner.
"""
import subprocess
import sys

if __name__ == "__main__":
    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", "tests", "-q", *sys.argv[1:]]))
