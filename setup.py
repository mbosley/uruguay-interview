"""
Setup configuration for Uruguay Active Listening AI Framework.
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="uruguay-active-listening",
    version="0.1.0",
    author="Mitchell Bosley",
    author_email="mbosley@example.com",
    description="AI-powered qualitative analysis framework for democratic participation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mbosley/uruguay-interview",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Sociology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "uruguay-pipeline=scripts.run_pipeline:main",
            "uruguay-batch=scripts.batch_process:main",
            "uruguay-quality=scripts.quality_check:main",
            "uruguay-export=scripts.export_deliverables:main",
        ],
    },
    include_package_data=True,
    package_data={
        "config": ["prompts/*.xml", "prompts/*.yaml", "database/*.sql", "dashboards/*.yaml"],
        "tests": ["fixtures/sample_interviews/*", "fixtures/expected_outputs/*"],
    },
)