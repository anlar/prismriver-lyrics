import logging


def init_logging(quiet, verbose, log_file):
    log_format = '%(asctime)s %(levelname)s [%(module)s] %(message)s'

    if quiet:
        log_level = logging.WARNING
    elif verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    if log_file:
        log_handlers = [logging.FileHandler(log_file), logging.StreamHandler()]
    else:
        log_handlers = [logging.StreamHandler()]

    logging.basicConfig(format=log_format, level=log_level, handlers=log_handlers)


def format_file_size(size_bytes):
    multiple = 1024
    for suffix in ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']:
        size = size_bytes / multiple
        if size < multiple:
            return '{0:.1f} {1}'.format(size, suffix)


def format_time_ms(time_sec):
    return "{:.1f} ms".format(time_sec * 1000)
