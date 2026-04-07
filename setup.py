from pathlib import Path

from setuptools import find_packages, setup


BASE_DIR = Path(__file__).parent


def read_requirements() -> list[str]:
    requirements_file = BASE_DIR / "requirements.txt"
    if not requirements_file.exists():
        return []

    requirements: list[str] = []
    for line in requirements_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            requirements.append(line)
    return requirements


setup(
    name="assistant-pro",
    version="0.1.0",
    description="A PyQt desktop assistant for task and money tracking.",
    packages=find_packages(include=["app", "app.*"]),
    py_modules=["main", "config", "logging_conf"],
    include_package_data=True,
    install_requires=read_requirements(),
    python_requires=">=3.10",
    entry_points={
        "gui_scripts": [
            "assistant-pro=main:main",
        ],
    },
)
