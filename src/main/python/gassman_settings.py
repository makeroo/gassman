'''
Created on 03/mar/2014

@author: makeroo
'''

DEBUG_MODE=True

HTTP_PORT=8180

DB_HOST='127.0.0.1'
DB_PORT=3306
DB_USER='gassman'
DB_PASSWORD='gassman'
DB_NAME='gassman'
DB_CHECK_INTERVAL=60*1000 # 1 minuto

COOKIE_SECRET='DEVELOPMENT_XSRF_SECRET'
COOKIE_MAX_AGE_DAYS=15

TRANSLATIONS_PATH='/Users/makeroo/personale/tmp_gas/gassman/src/main/translations/'
TEMPLATE_PATH='/Users/makeroo/personale/tmp_gas/gassman/src/main/tornado_templates/'
STATIC_PATH='/Users/makeroo/personale/tmp_gas/gassman/target/www/static/'

PUBLISHED_URL='http://localhost:8180'

GOOGLE_OAUTH2_CLIENTID='989424552810-e69up91er2e3ge8rjvvbqfsq93uclvfk.apps.googleusercontent.com'
GOOGLE_OAUTH2_SECRET='Rn5vy-PnS8qGseRoE4ss7bRO'
GOOGLE_OAUTH2_REDIRECT='http://localhost:8180/auth/google'

FB_APP_ID='TODO'
FB_APP_KEY='TODO'

SMTP_SERVER=None
SMTP_PORT=25
SMTP_SENDER=None
SMTP_RECEIVER=None
SMTP_NUM_THREADS=2
SMTP_QUEUE_TIMEOUT=3

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
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'simpleFormatter',
            'stream': 'ext://sys.stdout',
        },
        'accessHandler': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'simpleFormatter',
            'stream': 'ext://sys.stdout',
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
