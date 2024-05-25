#  Copyright (c) Benedek Szanyó 2023-2024. All rights reserved.
import atexit
import logging
import os
import signal
import sys
import time
from multiprocessing import freeze_support
from queue import Queue

import win32api

from bpe import colorama
from bpe.colorama import Fore
from bpe.equipments.console import Console
from bpe.equipments.console.HaloSpinner import HaloSpinner
from bpe.equipments.logging.Handlers import PipeLineHandler
from bpe.equipments.logging.LogCatServer import LogCatServer
from bpe.equipments.platform.ColorCollection import set_color_loop
from bpe.equipments.security.SymmetricFernet import SymmetricFernet
from bpe.pyconio import WHITE, BLACK, LIGHTGREEN, LIGHTCYAN, LIGHTRED, YELLOW, RED, \
    settitle, textcolor, textbackground, textcolors, backgroundcolors


def out(record):
    colors = highlight[record["levelno"]]

    # Formatting the log record:
    record['name'] = f"{record['name'][-NAME_LENGTH:]:<{NAME_LENGTH}}"
    record['levelname'] = f"{record['levelname'][-8:]: <8}"
    record['msg'] = str(record['msg']).replace("\n", " | ")
    print(f"{textcolors[colors[0]]}{backgroundcolors[colors[1]]}{record['asctime']} | {record['levelname']} | {record['name']} | {record['msg']}")


unicode_sup = Console.is_unicode_supported()

halo2 = HaloSpinner(text="Initializing",
                    spinner="dots",
                    color="cyan",
                    animation="marquee",
                    unicode_supported=unicode_sup)

halo2.start()

CURRENT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
LOGCAT_CRYPTOGRAPHY_CONFIGURATION_FILE_LOCATION = os.path.join(CURRENT_DIR, "logcat_hazmat.yaml")
LOGGING_CONFIGURATION_FILE_LOCATION = os.path.join(CURRENT_DIR, "logging.yaml")
NAME_LENGTH = 20

if __name__ == "__main__":
    freeze_support()
    settitle("LogCat Console")

    highlight = {0: [WHITE, BLACK],
                 10: [LIGHTGREEN, BLACK],
                 20: [LIGHTCYAN, BLACK],
                 30: [YELLOW, BLACK],
                 40: [LIGHTRED, BLACK],
                 50: [YELLOW, RED]}

    halo2.text = "Setting up console colors"

    set_color_loop(CURRENT_DIR, True)

    # color_test(0, 0)
    # print()

    # for logtype in highlight:
    #     textcolor(highlight[logtype][0])
    #     textbackground(highlight[logtype][1])
    #     print(f"Test color for logtype {logtype}.")

    textcolor(WHITE)
    textbackground(BLACK)

    halo2.text = "Cryptographic algorithm loading"

    cryptography_algorithm = SymmetricFernet()
    cryptography_algorithm.set_configuration_file_location(LOGCAT_CRYPTOGRAPHY_CONFIGURATION_FILE_LOCATION)
    cryptography_algorithm.load_configuration()

    halo2.text = "LogCat server starting"

    kwargs = {
        "child_logger_name": "logcatserver",
        "child_logger_level": logging.DEBUG,
        "logger_interface_configuration": LOGGING_CONFIGURATION_FILE_LOCATION
    }
    logcat_server = LogCatServer(**kwargs)
    logcat_server.set_cryptography_algorithm(cryptography_algorithm)
    internal_logger = Queue()

    halo2.text = "Internal logger pipeline setting up"

    for handler in logcat_server.Logger.handlers:
        if handler.name == "console" and isinstance(handler, PipeLineHandler):
            handler.set_pipeline(internal_logger)

    def kill():
        halo2.enabled = False
        print()
        logcat_server.close()

    signal.signal(signal.SIGINT, lambda sig, frame: kill())
    signal.signal(signal.SIGTERM, lambda sig, frame: kill())
    atexit.register(lambda: kill())
    win32api.SetConsoleCtrlHandler(lambda signal_type: kill(), True)

    halo2.clear()
    print(f"{Fore.GREEN}✔  Steady{Fore.RESET}")

    logcat_server.start()

    halo2.text = "Waiting for connection"
    halo2.spinner = "earth"
    halo2.interval = 500
    print()
    halo2.enabled = False

    while not logcat_server.is_connected():
        if logcat_server.is_closed():
            if halo2.enabled:
                halo2.enabled = False
            break
        while not internal_logger.empty():
            if halo2.enabled:
                halo2.enabled = False
            record = internal_logger.get()
            out(record)
        time.sleep(0.2)
        halo2.enabled = True

    halo2.text = "Connection alive!"
    halo2.text = "Waiting for connection"

    while not logcat_server.is_closed():
        while logcat_server.Queue.empty() and internal_logger.empty():
            if not logcat_server.is_connected():
                halo2.enabled = True
            time.sleep(0.1)

        if internal_logger.empty():
            record = logcat_server.Queue.get()
        else:
            record = internal_logger.get()
        if halo2.enabled:
            print()
        halo2.enabled = False
        out(record)

    logcat_server.join()
    halo2.stop_and_persist("Terminated!")
