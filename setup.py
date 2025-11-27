from setuptools import setup, find_packages

setup(
    name="llm-balance",
    version="0.2.7",
    description="Check LLM platform balance and usage via API keys and browser cookies",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "fire>=0.5.0",
        "requests>=2.31.0",
        "pycookiecheat>=0.5.0",
        "beautifulsoup4>=4.12.0",
        "PyYAML>=6.0",
        "volcengine-python-sdk==4.0.13",
    ],
    entry_points={
        "console_scripts": [
            "llm-balance=llm_balance.cli:main",
        ],
    },
    python_requires=">=3.8",
)