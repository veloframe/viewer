from setuptools import setup, find_packages

__version__ = "0.1.0"

setup(
    name="veloframe",
    version=__version__,
    description="A beautiful, full-screen photo frame application",
    author="Martin Maisey",
    packages=find_packages(),
    install_requires=[
        "PySide6",
        "Pillow",
        "PyYAML",
        "numpy",
    ],
    entry_points={
        "console_scripts": [
            "veloframe=veloframe.viewer.photo_frame:main",
        ],
    },
    package_data={
        "veloframe": ["viewer/config.yaml"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Multimedia :: Graphics :: Viewers",
    ],
    python_requires=">=3.8",
)
