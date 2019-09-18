from setuptools import find_packages, setup


setup(
    name="aiohttp_micro",
    version="0.1.0",
    packages=find_packages(),
    url="https://github.com/clayman74/aiohttp-micro",
    licence="MIT",
    author="Kirill Sumorokov",
    author_email="sumorokov.k@gmail.com",
    description="""
        Collection of useful things for `aiohttp.web`__-based microservices.
    """,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: AsyncIO",
    ],
    keywords="aiohttp-micro",
    install_requires=[
        "aiodns",
        "aiohttp",
        "click",
        "sentry-sdk",
        "ujson",
        "uvloop",
    ],
    extras_require={
        "lint": [
            "flake8",
            "flake8-bugbear",
            "flake8-builtins-unleashed",
            "flake8-comprehensions",
            "flake8-import-order",
            "flake8-pytest",
            "flake8-print",
            "mypy",
            "black",
        ],
        "test": ["coverage", "faker", "pytest", "pytest-aiohttp"],
    },
)
