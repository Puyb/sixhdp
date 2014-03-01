def send_mail(subject='', template=None, mail=None):
    #if self.paiement_complet and self.dossier_complet_auto:
    #    return
    ctx = { }
    subject = subject
    message = render_to_string(template, ctx)
    msg = EmailMessage(subject, message, 'organisation@6hdeparis.fr', [ mail ])
    msg.content_subtype = "html"
    msg.send()

def renumerote():
    l = []
    for e in Equipe.objects.all():
        e.numero = 0
        if e.nom.startswith('6h de Paris'):
            e.nom = ''
            l.append(e)
        e.save()
    for e in Equipe.objects.extra(select={
            'club_upper': 'UPPER(club)',
            'nom_upper': 'UPPER(nom)',
            'c': "CASE categorie WHEN 'IDH' THEN 1 WHEN 'IDF' THEN 1 WHEN 'DUX' THEN 2 WHEN 'DUF' THEN 2 ELSE 3 END"
        }, order_by=['c', 'club_upper', 'nom_upper', 'id']):
        e.numero = e.getNumero()
        e.save()
    for i in range(len(l)):
        l[i].nom = '6h de Paris %s' % i
        l[i].save()


