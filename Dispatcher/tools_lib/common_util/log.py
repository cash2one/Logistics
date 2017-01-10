#!/usr/bin/env python
# coding:utf-8

"""
只在单进程时正确工作.
"""
import os
import re
import sys
import time
import logging
from logging.handlers import RotatingFileHandler

VERSION = "1.0.0"


def init_log(mod_dir):
    logging_msg_format = '[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)s] %(message)s'
    logging_date_format = '%Y-%m-%d %H:%M:%S'
    level = logging.INFO
    logging.basicConfig(
        stream=sys.stdout,  # sys.stdout
        level=level,
        format=logging_msg_format,
        datefmt=logging_date_format)
    # 不让requests包log, 除非是warning以上
    logging.getLogger("pika").setLevel(logging.ERROR)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logger = logging.getLogger()

    # for example: business_logic_api/rate/logs/
    logs_path = os.path.abspath(os.path.join(mod_dir, "logs"))

    folders = str(mod_dir).split('/')
    prefix = {
        "api_gateway": "AG",
        "business_logic": "BL",
        "data_and_service": "DAS",
        "schedule": "SC",
    }[folders[-2]]
    mod_first_letter = folders[-1][0].upper()
    mod_rest_letters = folders[-1][1:].lower()
    if prefix == "AW":
        logger_file = os.path.join(logs_path, "%s_%s%s_API_Processor_%s" % (
            prefix, mod_first_letter, mod_rest_letters, os.getpid()))
    else:
        logger_file = os.path.join(logs_path, "%s_%s%s_API_Processor" % (prefix, mod_first_letter, mod_rest_letters))
    try:
        basedir = os.path.dirname(logger_file)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        open(logger_file, 'a').close()
    except EnvironmentError:
        print("Logger file not found or creation failed.")
        exit(-1)
    ch = RotatingFileHandlerCustomHeader(logger_file, mode='a', maxBytes=20 << 20, backupCount=2, encoding=None,
                                         delay=0, utc=False, header=None)
    ch.setFormatter(logging.Formatter(logging_msg_format))
    logger.addHandler(ch)
    print(("Logger file located at [%s]." % logger_file))


class RotatingFileHandlerCustomHeader(RotatingFileHandler, object):
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=0, utc=False,
                 header=None):
        super(RotatingFileHandlerCustomHeader, self).__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.suffix = "%Y-%m-%d_%H-%M-%S.log"
        self.ext_match = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}.log$")
        self.utc = utc
        self.header_msg = header

    def get_files_to_delete(self):
        # Determine the files to delete when rolling over.
        dir_name, base_name = os.path.split(self.baseFilename)
        file_names = os.listdir(dir_name)
        result = []
        prefix = base_name + "."
        prefix_len = len(prefix)
        for file_name in file_names:
            if file_name[:prefix_len] == prefix:
                suffix = file_name[prefix_len:]
                if self.ext_match.match(suffix):
                    result.append(os.path.join(dir_name, file_name))
        result.sort()
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[:len(result) - self.backupCount]
        return result

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        if self.utc:
            time_tuple = time.gmtime()
        else:
            time_tuple = time.localtime()
        dfn = self.baseFilename + "." + time.strftime(self.suffix, time_tuple)
        if os.path.exists(dfn):
            os.remove(dfn)
        # Issue 18940: A file may not have been created if delay is True.
        if os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, dfn)
        if self.backupCount > 0:
            for file_to_del in self.get_files_to_delete():
                os.remove(file_to_del)
        if not self.delay:
            self.stream = self._open()

    def shouldRollover(self, record):
        return super(RotatingFileHandlerCustomHeader, self).shouldRollover(record)

    def emit(self, record):
        """
        Emit a record.

        Output the record to the file, catering for rollover as described
        in doRollover().
        """
        try:
            if self.shouldRollover(record):
                self.doRollover()
                if self.header_msg is not None:
                    for msg in self.header_msg:
                        header_record = logging.LogRecord("", 20, "", 0, msg, (), None, None)
                        logging.FileHandler.emit(self, header_record)
            logging.FileHandler.emit(self, record)
        except (KeyboardInterrupt, SystemExit) as err:
            raise err
        except Exception as err:
            self.handleError(record)


if __name__ == "__main__":

    print((time.strftime("%Y-%m-%d_%H-%M-%S.log")))

    LOGGING_MSG_FORMAT = '%(name)-14s > [%(levelname)s] [%(asctime)s] : %(message)s'
    LOGGING_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    logging.basicConfig(stream=sys.stdout,
                        level=logging.INFO,
                        format=LOGGING_MSG_FORMAT,
                        datefmt=LOGGING_DATE_FORMAT)

    backup_msg = "Recording Processor Backed Up [7] messages."
    version_msg = str("Recording Processor Version %s" % VERSION)
    header_msg = [backup_msg, version_msg]

    logs_path = os.getcwd()
    test_logger = logging.getLogger()
    test_logger_file = os.path.join(logs_path, "rotate_logging_test")
    ch = RotatingFileHandlerCustomHeader(test_logger_file, mode='a', maxBytes=10, backupCount=2, encoding=None, delay=0,
                                         utc=False, header=header_msg)
    ch.setFormatter(logging.Formatter(LOGGING_MSG_FORMAT))
    test_logger.addHandler(ch)

    for i in range(1, 3):
        test_logger.info("log record number [%d].", i)
        time.sleep(1)

    ch.close()
    test_logger.removeHandler(ch)
