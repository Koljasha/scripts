#!/usr/bin/env python

#
# Шевелитель мышки
#

import pyautogui
import time
import random

SLEEP = 5

# Перемещение мыши в случайные координаты
while True:
    pyautogui.moveTo(random.randint(100, 1000), random.randint(100, 1000))
    time.sleep(SLEEP)

