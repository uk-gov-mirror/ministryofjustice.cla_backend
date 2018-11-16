from .base import *
import os

try:
    SECRET_KEY = os.environ["SECRET_KEY"]
except KeyError as e:
    print "Secret key not found, using a default key for the docker build step only, please set the SECRET_KEY in your environment"
    SECRET_KEY = "CHANGE_ME"
    pass

DEBUG = True if os.environ.get('SET_DEBUG') == 'True' else False

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('CLA', 'cla-alerts@digital.justice.gov.uk'),
)

MANAGERS = ADMINS

#HOST_NAME = "http://"

# LOGGING CONFIG FOR DOCKER ENV
LOGGING['handlers']['production_file'] = {
    'level' : 'INFO',
    'class' : 'logging.handlers.RotatingFileHandler',
    'filename' : '/var/log/wsgi/app.log',
    'maxBytes': 1024*1024*5, # 5 MB
    'backupCount' : 7,
    'formatter': 'logstash',
    'filters': ['require_debug_false'],
}

LOGGING['handlers']['debug_file'] = {
    'level' : 'DEBUG',
    'class' : 'logging.handlers.RotatingFileHandler',
    'filename' : '/var/log/wsgi/debug.log',
    'maxBytes': 1024*1024*5, # 5 MB
    'backupCount' : 7,
    'formatter': 'verbose',
    'filters': ['require_debug_true'],
}

LOGGING['loggers'][''] = {
    'handlers': ['production_file', 'debug_file', 'console'],
    'level': "DEBUG",
}
