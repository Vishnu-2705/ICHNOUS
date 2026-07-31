from setuptools import find_packages, setup

setup(
    name="tracemind",
    version="0.2.0",
    description="TraceMind Python SDK — Real-Time AI Agent Runtime Instrumentation & Causal Debugging",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="TraceMind Team",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.28.0",
        "httpx>=0.24.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
