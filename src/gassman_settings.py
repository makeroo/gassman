'''
Created on 03/mar/2014

@author: makeroo
'''

HTTP_PORT=8180

DB_HOST='127.0.0.1'
DB_PORT=3306
DB_USER=None
DB_PASSWORD=None
DB_NAME=None
DB_CHECK_INTERVAL=60*1000 # 1 minuto

COOKIE_SECRET='DEVELOPMENT_XSRF_SECRET'
COOKIE_MAX_AGE_DAYS=15

FB_APP_ID='TODO'
FB_APP_KEY='TODO'

SMTP_SERVER=None
SMTP_PORT=25
SMTP_SENDER='gassman@gassmanager.org'
SMTP_RECEIVER=None

LOG={
    'version': 1,
    'root': {
        'level': 'DEBUG',
        'handlers': [ 'codeHandler' ],
    },
    'loggers': {
        'tornado.access': {
            'level': 'DEBUG',
            'handlers': [ 'accessHandler' ],
            'qualname': 'access',
            'propagate': 0
        },
        'tornado.application': {
            'level': 'DEBUG',
            'handlers': [ 'codeHandler' ],
            'qualname': 'access',
            'propagate': 0
        },
        'tornado.general': {
            'level': 'DEBUG',
            'handlers': [ 'codeHandler' ],
            'qualname': 'access',
            'propagate': 0
        },
        'gassman.application': {
            'level': 'DEBUG',
            'handlers': [ 'codeHandler' ],
            'qualname': 'access',
            'propagate': 0
        },
    },
    'handlers': {
        'codeHandler': {
            'class': 'logging.StreamHandler', #'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'simpleFormatter',
            'stream': 'ext://sys.stdout',
            #'filename': /var/log/gassman_server.log',
        },
        'accessHandler': {
            'class': 'logging.StreamHandler', #'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'simpleFormatter',
            'stream': 'ext://sys.stdout',
             #'filename': /var/log/gassman_server_access.log',
        },
    },
    'formatters': {
        'simpleFormatter': {
            '()': 'loglib.ColoredFormatter',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '',
            'colors': {
                'CRITICAL': '$RED$BOLD',
                'FATAL': '$RED$BOLD',
                'ERROR': '$RED',
                'WARNING': '$YELLOW',
                'INFO': '',
                'DEBUG': '$CYAN',
            },
        },
    },
    }
