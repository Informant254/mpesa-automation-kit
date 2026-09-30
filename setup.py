from setuptools import find_packages, setup

setup(
    name="mpesa-automation-kit",
    version="0.2.0",
    description="Python toolkit for Safaricom M-Pesa Daraja automation",
    packages=find_packages(),
    install_requires=["requests", "python-dotenv", "fastapi", "uvicorn[standard]"],
    entry_points={"console_scripts": ["kenyapay=mpesa_kit.cli:main"]},
    python_requires=">=3.8",
)
