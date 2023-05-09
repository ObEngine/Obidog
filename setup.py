from setuptools import setup, find_packages
from os import path
from io import open

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="obidog",
    version="1.0.0",
    description="ÖbEngine's Lua Documentation Generator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Sygmei/Obidog",
    author="Sygmei",
    author_email="sygmei@outlook.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Documentation",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="obengine lua documentation generator",
    packages=find_packages(),
    install_requires=[
        "lxml",
        "GitPython",
        "requests",
        "mako",
        "inflection",
        "bs4",
        "semver",
        "pydantic"
    ],
    extras_require={
        "lint": ["flake8"],
    },
    entry_points={
        "console_scripts": [
            "obidog=obidog.main:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/Sygmei/Obidog/issues",
        "Source": "https://github.com/Sygmei/Obidog",
    },
)
