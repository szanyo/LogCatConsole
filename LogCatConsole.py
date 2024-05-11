#  Copyright (c) Benedek Szanyó 2023-2024. All rights reserved.
import logging
import os
import sys
import time
from queue import Queue

from bpe.equipments.logging.LogCatServer import LogCatServer
from bpe.equipments.platform.ColorCollection import set_color_loop
from bpe.equipments.security.SymmetricFernet import SymmetricFernet
from bpe.pyconio import clrscr, WHITE, BLACK, LIGHTGREEN, LIGHTCYAN, LIGHTRED, YELLOW, RED, \
    settitle, textcolor, textbackground
from utils.CustomLogging import PipeLineHandler


def out(record):
    colors = highlight[record["levelno"]]

    textcolor(colors[0])
    textbackground(colors[1])

    # Formatting the log record:
    record['name'] = f"{record['name'][-NAME_LENGTH:]:<{NAME_LENGTH}}"
    record['levelname'] = f"{record['levelname'][-8:]: <8}"
    print(f"{record['asctime']} | {record['levelname']} | {record['name']} | {record['msg']}")


CURRENT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
LOGCAT_CRYPTOGRAPHY_CONFIGURATION_FILE_LOCATION = os.path.join(CURRENT_DIR, "logcat_hazmat.yaml")
LOGGING_CONFIGURATION_FILE_LOCATION = os.path.join(CURRENT_DIR, "logging.yaml")
NAME_LENGTH = 20

settitle("LogCat Console")

highlight = {0: [WHITE, BLACK],
             10: [LIGHTGREEN, BLACK],
             20: [LIGHTCYAN, BLACK],
             30: [YELLOW, BLACK],
             40: [LIGHTRED, BLACK],
             50: [YELLOW, RED]}

set_color_loop(CURRENT_DIR, True)

# color_test(0, 0)
# print()

# for logtype in highlight:
#     textcolor(highlight[logtype][0])
#     textbackground(highlight[logtype][1])
#     print(f"Test color for logtype {logtype}.")

textcolor(WHITE)
textbackground(BLACK)

clrscr()

print("Initializing...")

cryptography_algorithm = SymmetricFernet()
cryptography_algorithm.set_configuration_file_location(LOGCAT_CRYPTOGRAPHY_CONFIGURATION_FILE_LOCATION)
cryptography_algorithm.load_configuration()

kwargs = {
    "child_logger_name": "logcatserver",
    "child_logger_level": logging.DEBUG,
    "logger_interface_configuration": LOGGING_CONFIGURATION_FILE_LOCATION
}
logcat_server = LogCatServer(**kwargs)
logcat_server.set_cryptography_algorithm(cryptography_algorithm)
internal_logger = Queue()

for handler in logcat_server.Logger.handlers:
    if handler.name == "console" and isinstance(handler, PipeLineHandler):
        handler.set_pipeline(internal_logger)

print("Waiting for connection...")

logcat_server.start()

while not logcat_server.is_connected():
    while not internal_logger.empty():
        record = internal_logger.get()
        out(record)
    time.sleep(0.2)

print("Connection alive!")

while logcat_server.is_alive():
    while logcat_server.Queue.empty() and internal_logger.empty():
        time.sleep(0.1)

    if internal_logger.empty():
        record = logcat_server.Queue.get()
    else:
        record = internal_logger.get()

    out(record)
