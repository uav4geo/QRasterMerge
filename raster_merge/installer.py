import pathlib
import sys
import os
import subprocess
import platform


def install_deps():
    plugin_dir = os.path.dirname(os.path.realpath(__file__))
    op = platform.system()
    sys.path.append(plugin_dir)

    with open(os.path.join(plugin_dir, "requirements.txt"), "r") as requirements:
        for dep in requirements.readlines():
            dep = dep.replace("\n", "")
            dep_noversion = dep.strip().split("==")[0]
            try:
                __import__(dep_noversion)
            except ImportError:
                if op == "Darwin":
                    import pip
                    pip.main(["install", dep])
                elif op == "Linux":
                    subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                elif op == "Windows":
                    subprocess.check_call(["python3", "-m", "pip", "install", dep])