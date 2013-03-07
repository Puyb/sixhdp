from settings import *

def settings(req):
    return {
        'YEAR':    YEAR,
        'MONTH':   MONTH,
        'DAY':     DAY,
        'TITLE':   TITLE,
        'MIN_AGE': MIN_AGE,
        'PAYPAL_URL':      PAYPAL_URL,
        'PAYPAL_BUSINESS': PAYPAL_BUSINESS,
    }
