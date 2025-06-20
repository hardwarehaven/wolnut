__version__ = '1.0.0'


def entrypoint():
    import logging

    from .__main__ import main

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
    )

    return main()
