#  Copyright (c) Benedek Szanyó 2024. All rights reserved.

import os
import sys

from bpe.equipments.security.SymmetricFernet import SymmetricFernet
from bpe.pyconio import settitle


def trim_word(path, word):
    if path.endswith(word):
        return path[:-len(word)].rstrip("\\/")
    return path


# trim LogCat from the path end
CURRENT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
LOGCAT_CONFIGURATION_FILE_LOCATION = os.path.join(CURRENT_DIR, "logcat_hazmat.yaml")

settitle("LogCat Cryptography Editor")

cryptography_algorithm = SymmetricFernet()
cryptography_algorithm.set_configuration_file_location(LOGCAT_CONFIGURATION_FILE_LOCATION)
cryptography_algorithm.load_configuration()

print("Cryptography algorithm loaded.")
print("New key param generation...")

cryptography_algorithm.generate_salt(16)

print("New salt generated.")
print("New password generation...")

cryptography_algorithm.generate_password(16)

print("Save configuration...")

cryptography_algorithm.save_configuration()

print("Configuration saved.")
print("Goodbye!")
