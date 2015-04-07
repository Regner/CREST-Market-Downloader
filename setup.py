

from pip.req    import parse_requirements
from setuptools import setup, find_packages

from crestmarketdownloader import __version__

install_reqs = parse_requirements('requirements.txt')
reqs         = [str(ir.req) for ir in install_reqs]

setup(
    name='crest-market-downloader',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=reqs,
    entry_points='''
        [console_scripts]
        crestmarketdownloader=crestmarketdownloader.downloader:main
    ''',
)