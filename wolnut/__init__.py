__title__ = 'wolnut'
__author__ = 'hardwarehaven'
__license__ = 'MIT'
__copyright__ = 'Copyright 2025 hardwarehaven'
__version__ = '1.0.0'


def entrypoint():
    import logging

    from .__main__ import main

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
    )

    return main()
