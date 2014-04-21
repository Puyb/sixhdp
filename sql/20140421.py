from inscriptions.models import *
import re

r = re.compile('{% *url +([a-z._]+)', re.I)
for t in TemplateMail.objects.all():
    t.sujet = r.sub('{% url "\\1"', t.sujet)
    t.message = r.sub('{% url "\\1"', t.message)
    t.save()

