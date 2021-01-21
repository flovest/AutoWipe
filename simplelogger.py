import os
from enum import IntEnum
from datetime import datetime as dt

class SimpleLogger(object):

    def __init__(self, logger_name, log_file, log_level, append_date_to_logfile_name=True, datetime_format=None):
        self.logger_name = logger_name
        self.log_file = log_file
        self.log_level = log_level

        if self.log_file is not None:
            self.log_file_dir = os.path.dirname(self.log_file)
            self.log_file_name = os.path.basename(self.log_file)

        if datetime_format is None:
            datetime_format = "%Y-%m-%d %H:%M:%S.%f"
        self.datetime_format = datetime_format

    def log(self, log_message, log_level):
        if (log_level <= self.log_level):
            full_log_message = "[{0}][{1}][{2}]: {3}".format(dt.now().strftime(self.datetime_format), log_level.name, self.logger_name, log_message)
            print(full_log_message)
            self._log_to_file(full_log_message)

    def _log_to_file(self, full_log_message):
        if self.log_file is not None:

            splitted_name = self.log_file.split('.')
            log_file_location = "{0}.{1}.{2}".format(".".join(splitted_name[:-1]), dt.now().strftime("%Y-%m-%d"), splitted_name[-1])


            if not os.path.isfile(log_file_location):
                with open(log_file_location, 'w'): pass

            dir_fd = os.open(log_file_location, os.O_RDONLY)

            def opener(path, flags):
                return os.open(path, flags, dir_fd=dir_fd)

            with open(log_file_location, 'a', opener=opener) as f:
                print(full_log_message, file=f)
            
            os.close(dir_fd)


class LogLevel(IntEnum):
    FATAL=1
    ERROR=2
    WARN=3
    INFO=4
    DEBUG=5
    TRACE=6