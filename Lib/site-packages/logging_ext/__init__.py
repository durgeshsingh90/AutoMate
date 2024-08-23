#!/usr/bin/env python3

'''
logging ext module;
'''

import logging
import types

##  ============================================================================
##  custom logging levels;
##  ============================================================================

DEBUG   = logging.DEBUG
VERBOSE = logging.INFO - 1
INFO    = logging.INFO
WARN    = logging.WARN
ERROR   = logging.ERROR

##  ============================================================================
##  add custom logging levels with names;
##  ============================================================================

logging.addLevelName(DEBUG,   'DEBUG'  )
logging.addLevelName(VERBOSE, 'VERBOSE')
logging.addLevelName(INFO,    'INFO'   )
logging.addLevelName(WARN,    'WARN'   )
logging.addLevelName(ERROR,   'ERROR'  )

##  ============================================================================
##  1-letter logging methods;
##  ============================================================================

def d(msg, *args, **kwargs):

    '''
    log a message at debug level;
    '''

    return logging.log(DEBUG, msg, *args, **kwargs)

def v(msg, *args, **kwargs):

    '''
    log a message at verbose level;
    '''

    return logging.log(VERBOSE, msg, *args, **kwargs)

def i(msg, *args, **kwargs):

    '''
    log a message at info level;
    '''

    return logging.log(INFO, msg, *args, **kwargs)

def w(msg, *args, **kwargs):

    '''
    log a message at warn level;
    '''

    return logging.log(WARN, msg, *args, **kwargs)

def e(msg, *args, **kwargs):

    '''
    log a message at error level;
    '''

    return logging.log(ERROR, msg, *args, **kwargs)

##  ============================================================================
##  functions;
##  ============================================================================

def getLogger(name=None):

    '''
    return a logger instrumented with additional 1-letter logging methods;
    '''

    logger = logging.getLogger(name=name)

    if not hasattr(logger, 'd'):
        def d(self, msg, *args, **kwargs):
            return self.log(DEBUG, msg, *args, **kwargs)
        logger.d = types.MethodType(d, logger)

    if not hasattr(logger, 'v'):
        def v(self, msg, *args, **kwargs):
            return self.log(VERBOSE, msg, *args, **kwargs)
        logger.v = types.MethodType(v, logger)

    if not hasattr(logger, 'i'):
        def i(self, msg, *args, **kwargs):
            return self.log(INFO, msg, *args, **kwargs)
        logger.i = types.MethodType(i, logger)

    if not hasattr(logger, 'w'):
        def w(self, msg, *args, **kwargs):
            return self.log(WARN, msg, *args, **kwargs)
        logger.w = types.MethodType(w, logger)

    if not hasattr(logger, 'e'):
        def e(self, msg, *args, **kwargs):
            return self.log(ERROR, msg, *args, **kwargs)
        logger.e = types.MethodType(e, logger)

    return logger

