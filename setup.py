from setuptools import setup, find_packages
import pathlib

README = (pathlib.Path(__file__).parent / "README.md").read_text()

setup(
    name="Lomino",
    version="0.1",
    url="https://github.com/L0Rd5/Lomino/tree/main/Lomino",
    download_url="https://github.com/L0Rd5/Lomino/archive/refs/heads/main.zip",
    description="Amino Api Library",
    long_description=README,
    author="L0Rd5",
    license="MIT",
    keywords=[
        "Amino",
        "python",
        "python3",
        "python3.x",
        "L0Rd5",
        "Lord",
        "Lomino",
        "lomino",
        "Lomino python"
        "bots",
        "narvii",
    ],
    include_package_data=True,
    install_requires=[
        "requests",
        "setuptools",
    ],
    setup_requires=["wheel"],
    packages=find_packages(),
)
