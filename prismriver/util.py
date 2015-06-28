def format_file_size(size_bytes):
    multiple = 1024
    for suffix in ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']:
        size = size_bytes / multiple
        if size < multiple:
            return '{0:.1f} {1}'.format(size, suffix)


def format_time_ms(time_sec):
    return "{:.1f} ms".format(time_sec * 1000)
