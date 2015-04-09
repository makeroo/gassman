# coding=UTF-8

import sys
import logging
import re
import traceback

_reset = '\033[0m'
_colors = dict([ (k if i < 8 else 'BG_%s' % k, '\033[%dm' % (30 + i if i < 8 else 32 + i)) for i, k in enumerate(['BLACK', 'RED', 'GREEN', 'YELLOW', 'BLUE', 'MAGENTA', 'CYAN', 'WHITE'] * 2) ])
_colors['RESET'] = '\033[0m'
_colors['BOLD'] = '\033[1m'

_rx = re.compile(r'\$(BLACK|RED|GREEN|YELLOW|BLUE|MAGENTA|CYAN|WHITE|BG_BLACK|BG_RED|BG_GREEN|BG_YELLOW|BG_BLUE|BG_MAGENTA|BG_CYAN|BG_WHITE|RESET|BOLD)')

def formatter_message (message, use_color=True):
    for s, e, k in reversed([ (m.start(), m.end(), m.group()[1:]) for m in  re.finditer(_rx, message) ]):
        message = message[:s] + (_colors[k] if use_color else '') + message[e:]
    return message

class ColoredFormatter (logging.Formatter):
    def __init__ (self, colors={}, *args, **kwargs):
        self.oldsuper = sys.hexversion < 0x02070000
        if self.oldsuper:
            logging.Formatter.__init__(self, *args, **kwargs) # python 2.6
        else:
            super(ColoredFormatter, self).__init__(*args, **kwargs) # python >=2.7
        self.colors = colors

    def format (self, record):
        color = self.colors.get(record.levelname, '')
        if self.oldsuper:
            s = logging.Formatter.format(self, record)
        else:
            s = super(ColoredFormatter, self).format(record)
        return formatter_message(color + s + _reset, self.colors)

class TracebackFormatter (object):
    def __init__ (self, tb):
        self.tb = tb

    def __str__ (self):
        return ''.join(traceback.format_tb(self.tb))
