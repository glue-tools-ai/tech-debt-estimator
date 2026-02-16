from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tech-debt-estimator",
    version="0.1.0",
    author="Glue",
    author_email="hello@getglueapp.com",
    description="Quantify technical debt in developer-hours from code metrics and git history",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/glue-tools-ai/tech-debt-estimator",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
    ],
    python_requires=">=3.8",
    install_requires=[
        "gitpython>=3.1.0",
        "click>=8.0.0",
        "rich>=10.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.12",
            "black>=21.0",
            "flake8>=3.9",
            "mypy>=0.910",
        ],
    },
    entry_points={
        "console_scripts": [
            "tech-debt=tech_debt_estimator.cli:main",
        ],
    },
    include_package_data=True,
)
