'''
Created on 03/mar/2014

@author: makeroo
'''

HTTP_PORT=8180

DB_HOST=''
DB_PORT=3306
DB_USER='gassman'
DB_PASSWORD='gassman'
DB_NAME='gassman'

COOKIE_SECRET='DEVELOPMENT_XSRF_SECRET'

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
