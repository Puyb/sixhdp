from settings import *

def settings(req):
    return {
        'YEAR':    YEAR,
        'MONTH':   MONTH,
        'DAY':     DAY,
        'TITLE':   TITLE,
        'MIN_AGE': MIN_AGE,
        'MAX_EQUIPIER': MAX_EQUIPIER,
        'CLOSE_YEAR':  CLOSE_YEAR,
        'CLOSE_MONTH': CLOSE_MONTH,
        'CLOSE_DAY':   CLOSE_DAY,
        'PAYPAL_URL':      PAYPAL_URL,
        'PAYPAL_BUSINESS': PAYPAL_BUSINESS,
    }
