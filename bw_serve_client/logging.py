import logging

"""
The BSCLogger class provides a flexible logging setup for the bw-serve-client
library.  It defaults to a dual logging system that logs both to a file
('bw-serve-client.log') and the console.

Users can pass their own logger if they prefer a different logging setup,
assuming it supports the standard log levels (debug, info, warning, error,
critical).

Example of using a custom logger with a SyslogHandler:

    import logging
    import logging.handlers

    custom_logger = logging.getLogger('customLogger')
    syslog_handler = logging.handlers.SyslogHandler(address='/dev/log')
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    syslog_handler.setFormatter(formatter)
    custom_logger.addHandler(syslog_handler)
    custom_logger.setLevel(logging.WARNING)

    logger_instance = BSCLogger(logger=custom_logger)
    logger_instance.warning('This is a warning message')
"""
class BSCLogger:
    def __init__(self, logger=None):
        if logger is None:
            self.logger = logging.getLogger('bw-serve-client')
            file_handler = logging.FileHandler('bw-serve-client.log')
            stream_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.addHandler(stream_handler)
            self.logger.setLevel(logging.INFO)
        else:
            self.logger = logger

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)
