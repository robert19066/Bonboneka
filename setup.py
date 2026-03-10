from setuptools import setup, find_packages

setup(
    name="bonboneka",
    version="0.1.0",
    description="Bundle HTML/CSS/JS into an Android WebView app",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Brickboss",
    author_email="info@example.com",
    url="https://github.com/yourusername/bonboneka",
    license="MIT",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "Pillow>=10.0.0",
    ],
    entry_points={
        "console_scripts": [
            "bomk=bomk.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    keywords="android webview app builder html css javascript",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/bonboneka/issues",
        "Source": "https://github.com/yourusername/bonboneka",
    },
)