import urlparse, re
from threading import Thread
#from django.template.loader import render_to_string
#from django.core.mail import EmailMessage

def urlEncodeNonAscii(b):
    return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

def iriToUri(iri):
    parts = urlparse.urlparse(iri)
    return urlparse.urlunparse(
        part.encode('idna') if parti==1 else urlEncodeNonAscii(part.encode('utf-8'))
        for parti, part in enumerate(parts)
    )

class MailThread(Thread):
    def __init__ (self, messages):
        Thread.__init__(self)
        self.messages = messages

    def run(self):  
        for message in self.messages:
            message.send()

# def renumerote():
#     l = []
#     for e in Equipe.objects.all():
#         e.numero = 0
#         if e.nom.startswith('6h de Paris'):
#             e.nom = ''
#             l.append(e)
#         e.save()
#     for e in Equipe.objects.extra(select={
#             'club_upper': 'UPPER(club)',
#             'nom_upper': 'UPPER(nom)',
#             'c': "CASE categorie WHEN 'IDH' THEN 1 WHEN 'IDF' THEN 1 WHEN 'DUX' THEN 2 WHEN 'DUF' THEN 2 ELSE 3 END"
#         }, order_by=['c', 'club_upper', 'nom_upper', 'id']):
#         e.numero = e.getNumero()
#         e.save()
#     for i in range(len(l)):
#         l[i].nom = '6h de Paris %s' % i
#         l[i].save()


