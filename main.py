# _*_ coding:utf8 _*_

import time
import datetime
from scrapy.cmdline import execute

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
execute(["scrapy","crawl","jobbole"])

def test():
    pass

