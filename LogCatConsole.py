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

from bpe.colorama import Fore
from bpe.utils.console import Console
from bpe.utils.console.HaloSpinner import HaloSpinner
from bpe.utils.logging.Handlers import PipeLineHandler
from bpe.utils.logging.LogCatServer import LogCatServer
from bpe.utils.platform.ColorCollection import set_color_loop
from bpe.utils.platform.ScreenSize import get_terminal_size
from bpe.utils.security.SymmetricFernet import SymmetricFernet
from bpe.pyconio import WHITE, BLACK, LIGHTGREEN, LIGHTCYAN, LIGHTRED, YELLOW, RED, \
    settitle, textcolor, textbackground, textcolors, backgroundcolors


def build_time_component(record):
    return record['asctime']


def build_level_component(record):
    return f"{record['levelname'][-8:]: <8}"


def build_name_component(record):
    name = []
    if len(record['name']) > NAME_LENGTH:
        # split name into lines
        remaining_name = record['name']
        while len(remaining_name) > NAME_LENGTH:
            temp = remaining_name[:NAME_LENGTH]
            last_dot = temp.rfind(".")
            if last_dot > 0:
                name.append(f"{temp[:last_dot + 1]:<{NAME_LENGTH}}")
                remaining_name = remaining_name[last_dot + 1:]
            else:
                name.append(f"{temp:<{NAME_LENGTH}}")
                remaining_name = remaining_name[NAME_LENGTH:]
            if len(remaining_name) < NAME_LENGTH:
                name.append(f"{remaining_name:<{NAME_LENGTH}}")

    else:
        name.append(f"{record['name'][-NAME_LENGTH:]:<{NAME_LENGTH}}")

    return name


def build_msg_component(record):
    msg = []
    if len(str(record['message'])) > MSG_LENGTH:
        # split message into lines
        remaining_msg = str(record['message'])

        # remaining_msg = remaining_msg.replace("\n", "NewLine")

        while len(remaining_msg) > 0:
            temp = remaining_msg[:MSG_LENGTH]
            last_space = temp.rfind(" ")
            first_newline = temp.find("\n")
            first_double_newline = temp.find("\n\n")

            if first_double_newline > 0:
                sub_msg = remaining_msg[:first_double_newline] + " " * (MSG_LENGTH - first_double_newline)
                msg.append(sub_msg)
                msg.append(EMPTY_MSG_COMPONENT)
                remaining_msg = remaining_msg[first_double_newline + 2:]
            elif first_newline > 0:
                sub_msg = remaining_msg[:first_newline] + " " * (MSG_LENGTH - first_newline)
                msg.append(sub_msg)
                remaining_msg = remaining_msg[first_newline + 1:]
            elif last_space > 0:
                sub_msg = remaining_msg[:last_space] + " " * (MSG_LENGTH - last_space)
                msg.append(sub_msg)
                remaining_msg = remaining_msg[last_space + 1:]
            else:
                sub_msg = remaining_msg[:MSG_LENGTH]
                sub_msg = sub_msg + " " * (MSG_LENGTH - len(sub_msg))
                msg.append(sub_msg)
                remaining_msg = remaining_msg[MSG_LENGTH:]
    else:
        msg.append(str(record['message']))

    return msg


def out(record):
    colors = highlight[record["levelno"]]

    # line components
    time = build_time_component(record)
    level = build_level_component(record)
    name = build_name_component(record)
    msg = build_msg_component(record)

    # build lines
    lines = []
    name_index = 0
    msg_index = 0
    while name_index < len(name) or msg_index < len(msg):
        if name_index == 0 and msg_index == 0:
            lines.append(f"{time}{SEP}{level}{SEP}{name[0]}{SEP}{msg[0]}")
        else:
            name_component = EMPTY_NAME_COMPONENT
            msg_component = EMPTY_MSG_COMPONENT
            if name_index < len(name):
                name_component = name[name_index]
            if msg_index < len(msg):
                msg_component = msg[msg_index]
            lines.append(f"{EMPTY_TIME_COMPONENT}{SEP}{EMPTY_LEVEL_COMPONENT}{SEP}{name_component}{SEP}{msg_component}")
        if name_index < len(name):
            name_index += 1
        if msg_index < len(msg):
            msg_index += 1

    # print lines
    for line in lines:
        print(f"{textcolors[colors[0]]}{backgroundcolors[colors[1]]}{line}")




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

terminal_size = get_terminal_size()
print(f"Terminal size: {terminal_size}")
if terminal_size[0] < 120 or terminal_size[1] < 30:
    print("Terminal size is too small! Please resize to at least 120x24.")
    terminal_size = (120, 30)

# sample: 2024-05-25 16:31:36,372
SEP = " | "
SEPARATOR_LENGTH = len(SEP)
ASCTIME_LENGTH = 23
LEVEL_LENGTH = 8
NAME_LENGTH = 20
MSG_LENGTH = terminal_size[0] - ASCTIME_LENGTH - LEVEL_LENGTH - NAME_LENGTH - 3 * SEPARATOR_LENGTH

EMPTY_TIME_COMPONENT = " " * ASCTIME_LENGTH
EMPTY_LEVEL_COMPONENT = " " * LEVEL_LENGTH
EMPTY_NAME_COMPONENT = " " * NAME_LENGTH
EMPTY_MSG_COMPONENT = " " * MSG_LENGTH

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
