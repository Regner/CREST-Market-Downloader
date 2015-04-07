

from crestmarketdownloader import downloader

__version__    = '0.0.1'
__user_agent__ = 'CREST Market Downloader v{}'.format(__version__)
__base_url__   = 'http://public-crest-sisi.testeveonline.com'
__servers__    = {
    'Tranquility' : '',
    'Singularity' : 'http://public-crest-sisi.testeveonline.com',
}

downloader._user_agent = __user_agent__
downloader._base_url   = __base_url__
downloader._servers    = __servers__