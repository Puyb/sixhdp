from settings import *
from models import Course
from django.db.models import Min, Max

def course(request):
    course = (Course.objects
        .prefetch_related('categories')
        .annotate(min_age=Min('categories__min_age'), max_equipiers=Max('categories__max_equipiers'))
        .filter(uid=request.path.split('/')[1]))
    if not len(course):
        return ()
    return {
        'COURSE':          course[0],
        'YEAR':            course[0].date.year,
        'MONTH':           course[0].date.month,
        'DAY':             course[0].date.day,
        'TITLE':           course[0].nom,
        'MIN_AGE':         course[0].min_age,
        'MAX_EQUIPIERS':   course[0].max_equipiers,
        'CLOSE_YEAR':      course[0].date_fermeture.year,
        'CLOSE_MONTH':     course[0].date_fermeture.month,
        'CLOSE_DAY':       course[0].date_fermeture.day,
        'PAYPAL_BUSINESS': course[0].paypal,
    }

def settings(request):
    return {
        'PAYPAL_URL':      PAYPAL_URL,
        'ROOT_URL':        ROOT_URL,
    }
