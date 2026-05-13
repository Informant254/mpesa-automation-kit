from setuptools import setup, find_packages

setup(
    name="mpesa-automation-kit",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["requests", "python-dotenv", "httpx", "fastapi", "uvicorn", "pydantic"],
    entry_points={
        "console_scripts": [
            "kenyapay=mpesa_kit.cli:main",
        ],
    },
    python_requires=">=3.8",
)