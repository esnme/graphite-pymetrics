from distutils.core import setup

f = open("README.rst")
try:
    README = f.read()
finally:
    f.close()

setup(
    name="graphite-pymetrics",
    version="0.1.1",
    description = "A simple Python metrics framework to use with carbon/graphite.",
    long_description = README,
    author="Ronnie Kolehmainen",
    author_email="ronnie@esn.me",
    url="http://www.esn.me",
    download_url="http://github.com/esnme/graphite-pymetrics",
    license="MIT",
    platforms=["any"],
    packages=["metrics", "metrics.test"],
    install_requires=["pystatsd==0.1.6", "gevent"],
    classifiers=[
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Intended Audience :: Developers"
    ]
)
