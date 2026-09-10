from setuptools import setup, find_packages

setup(
    name="netkit-cli",
    version="1.0.0",
    description="Network Diagnostic Toolkit - WiFi Doctor, Network Mapper & Service Monitor",
    author="Khaled Noaman",
    author_email="khalednoaman@example.com",
    url="https://github.com/KHALEDNOAMAN/NetKit",
    packages=find_packages(),
    install_requires=[
        "click>=8.1", "rich>=13.0", "scapy>=2.5", "psutil>=5.9",
        "httpx>=0.26", "netifaces>=0.11", "flask>=3.0",
        "flask-socketio>=5.3", "pyyaml>=6.0",
    ],
    entry_points={"console_scripts": ["netkit=netkit.cli:main"]},
    python_requires=">=3.10",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: System :: Networking :: Monitoring",
    ],
)
