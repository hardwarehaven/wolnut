__version__ = '1.0.0'
from .__main__ import main  # re-export

__all__ = ('entrypoint', 'main')


def entrypoint():
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
    )

    return main()
