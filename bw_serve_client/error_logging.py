import logging

class ErrorLogger:

  """
    A class for managing errors and logging with support for custom error handling and logging objects.
    If no custom handlers are provided, implements minimal error handling and logging.

    Attributes:
        error_handler: An optional custom error handler object.
        logger: An optional custom logger object or Python's standard logging object if not provided.
        error_level: The minimum level of errors to handle.
        log_level: The minimum level of logs to record.
    """

  def __init__(
      self,
      error_handler=None,
      logger=None,
      error_level=logging.ERROR,
      log_level=logging.INFO
  ):
    """
        Initializes the ErrorLogger with optional error handling and logging objects.
        Sets up minimal error handling and logging if none are provided.
        """
    self.error_handler = error_handler
    self.logger = logger or logging.getLogger(__name__)
    self.error_level = error_level
    self.log_level = log_level

    # Configure the logger
    logging.basicConfig(level=self.log_level)

    def log(self, message, level=logging.INFO):
        """
        Logs a message with the specified logging level.

        :param message: The message to log.
        :param level: The logging level (e.g., logging.INFO, logging.ERROR).
        """
        if level >= self.log_level:
            self.logger.log(level, message)

    def handle_error(self, error, level=logging.ERROR):
        """
        Handles an error based on the specified error level.

        :param error: The error to handle.
        :param level: The error level (e.g., logging.ERROR).
        """
        if level >= self.error_level:
            if self.error_handler:
                self.error_handler(error, level)
            else:
                self.log(f"Error: {error}", level)

