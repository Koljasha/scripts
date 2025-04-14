#!/usr/bin/env python

#
# Шевелитель мышки
#
# pip install pyautogui
#
# sudo pacman -S tk
# sudo apt-get install python3-tk python3-dev
#

import pyautogui
import time
import random

SLEEP = 5

# Перемещение мыши в случайные координаты
while True:
    pyautogui.moveTo(random.randint(100, 1000), random.randint(100, 1000))
    time.sleep(SLEEP)

