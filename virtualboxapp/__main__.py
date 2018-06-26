import logging
from . import logger, verify_apps, run, vbox


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('apps', nargs='+')
    args = parser.parse_args()

    handler = logging.StreamHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    vbox_logger = logging.getLogger('vbox')
    vbox_logger.setLevel(logging.DEBUG)
    vbox_logger.addHandler(handler)
    run(*[app for app in verify_apps(vbox.VBox(extraPath=['/usr/local/bin']), *args.apps)])


if __name__ == "__main__":
    main()
