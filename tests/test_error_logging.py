import unittest
import logging
from bw_serve_client.error_logging import ErrorLogger


class TestErrorLogger(unittest.TestCase):

  def test_log_message(self):
    logger = ErrorLogger(log_level=logging.DEBUG)
    with self.assertLogs(level='DEBUG') as log:
      logger.log("Test debug message", logging.DEBUG)
      self.assertIn("Test debug message", log.output[0])

  def test_handle_error_with_custom_handler(self):

    def custom_error_handler(error, level):
      logging.getLogger().log(level, f"Custom error handler: {error}")

    logger = ErrorLogger(
      error_handler=custom_error_handler, error_level=logging.WARNING
    )
    with self.assertLogs(level='WARNING') as log:
      logger.handle_error("Test warning", logging.WARNING)
      self.assertIn("Custom error handler: Test warning", log.output[0])


if __name__ == '__main__':
  unittest.main()
