# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django_countries import CountryField
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
import os, re, urllib, urlparse, simplejson
from django.db import models
from settings import *
from datetime import date
from decimal import Decimal
from django.utils.safestring import mark_safe

# CATEGORIES = {
#     'SLH': { 'prix' : 50 },
#     'SLF': { 'prix' : 50 },
#     'DUO': { 'prix' : 80 },
#     'SNH': { 'prix' : 80 },
#     'SNF': { 'prix' : 80 },
#     'SNX': { 'prix' : 80 },
#     'VEH': { 'prix' : 80 },
#     'VEF': { 'prix' : 80 },
# }

SEXE_CHOICES = (
    ('H', _(u'Homme')),
    ('F', _(u'Femme'))
)

JUSTIFICATIF_CHOICES = (
    ('licence',    _(u'Licence FFRS 2013')),
    ('certificat', _(u'Certificat médical établi après le 4/08/2012'))
)

class Ville(models.Model):
    lat = models.DecimalField(max_digits=10, decimal_places=7)
    lng = models.DecimalField(max_digits=10, decimal_places=7)
    nom = models.CharField(max_length=200)
    region = models.CharField(max_length=200)
    pays = models.CharField(max_length=200)
    response = models.CharField(max_length=65535)

def lookup_ville(nom, cp, pays):
    nom = nom.lower()
    nom = re.sub('[- ,/]+', ' ', nom)
    try:
        return Ville.objects.get(nom=nom)
    except Ville.DoesNotExist, e:
        pass

    def urlEncodeNonAscii(b):
        return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

    def iriToUri(iri):
        parts = urlparse.urlparse(iri)
        return urlparse.urlunparse(
            part.encode('idna') if parti==1 else urlEncodeNonAscii(part.encode('utf-8'))
            for parti, part in enumerate(parts)
        )

    f = urllib.urlopen(iriToUri('http://open.mapquestapi.com/geocoding/v1/address?key=%s&location=%s' % (MAPQUEST_API_KEY, nom + ' ' + cp + ', ' + str(pays))))
    data = simplejson.load(f)
    f.close()

    if('results' not in data or
       not len(data['results']) or
       'locations' not in data['results'][0] or
       not len(data['results'][0]['locations'])):
        f = urllib.urlopen(iriToUri('http://open.mapquestapi.com/geocoding/v1/address?key=%s&location=%s' % (MAPQUEST_API_KEY, nom + ', ' + str(pays))))
        data = simplejson.load(f)
        f.close()

        if('results' not in data or
           not len(data['results']) or
           'locations' not in data['results'][0] or
           not len(data['results'][0]['locations'])):
            return None

    data = data['results'][0]['locations'][0]
    data['latLng']['lat'] = str(data['latLng']['lat'])
    data['latLng']['lng'] = str(data['latLng']['lng'])
    try:
        return Ville.objects.get(lat=data['latLng']['lat'], lng=data['latLng']['lng'])
    except Ville.DoesNotExist, e:
        pass
    obj = Ville(
        lat      = data['latLng']['lat'],
        lng      = data['latLng']['lng'],
        nom      = data['adminArea5'],
        region   = data['adminArea3'],
        pays     = data['adminArea1'],
        response = simplejson.dumps(data)
    )
    obj.save()
    return obj

class Equipe(models.Model):
    nom                = models.CharField(_(u"Nom d'équipe"), max_length=30)
    club               = models.CharField(_(u'Club'), max_length=30, blank=True)
    gerant_nom         = models.CharField(_(u'Nom'), max_length=200)
    gerant_prenom      = models.CharField(_(u'Prénom'), max_length=200)
    gerant_adresse1    = models.CharField(_(u'Adresse'), max_length=200, blank=True)
    gerant_adress2     = models.CharField(_(u'Adresse 2'), max_length=200, blank=True)
    gerant_ville       = models.CharField(_(u'Ville'), max_length=200)
    gerant_code_postal = models.CharField(_(u'Code postal'), max_length=200)
    gerant_pays        = CountryField(_(u'Pays'), default='FR')
    gerant_email       = models.EmailField(_(u'e-mail'), max_length=200)
    password           = models.CharField(_(u'Mot de passe'), max_length=200, blank=True)
    gerant_telephone   = models.CharField(_(u'Téléphone'), max_length=200, blank=True)
    categorie          = models.CharField(_(u'Catégorie'), max_length=10)
    nombre             = models.IntegerField(_(u"Nombre d'équipiers"))
    paiement_info      = models.CharField(_(u'Détails'), max_length=200, blank=True)
    prix               = models.DecimalField(_(u'Prix'), max_digits=5, decimal_places=2)
    paiement           = models.DecimalField(_(u'Paiement reçu'), max_digits=5, decimal_places=2, null=True, blank=True)
    dossier_complet    = models.NullBooleanField(_(u'Dossier complet'))
    date               = models.DateTimeField(_(u"Date d'insciption"), auto_now_add=True)
    commentaires       = models.TextField(_(u'Commentaires'), blank=True)
    gerant_ville2      = models.ForeignKey(Ville, null=True)
    numero             = models.IntegerField(_(u'Numéro'))

    def __unicode__(self):
        return u'%s - %s - %s' % (self.id, self.categorie, self.nom)

    def licence_manquantes(self):
        return [equipier for equipier in self.equipier_set.all() if equipier.justificatif == 'licence' and not equipier.piece_jointe_valide and not equipier.piece_jointe ]

    def certificat_manquantes(self):
        return [equipier for equipier in self.equipier_set.all() if equipier.justificatif == 'certificat' and not equipier.piece_jointe_valide and not equipier.piece_jointe ]

    def autorisation_manquantes(self):
        return [equipier for equipier in self.equipier_set.all() if equipier.age() < 18 and not equipier.autorisation_valide and not equipier.autorisation ]

    def documents_manquants2(self):
        return (len(self.licence_manquantes()) + len(self.certificat_manquantes()) + len(self.autorisation_manquantes())) or ''
    documents_manquants2.short_description = u'✉'

    def verifier(self):
        return len([equipier for equipier in self.equipier_set.all() 
                if (equipier.piece_jointe and equipier.piece_jointe_valide == None) or
                   (equipier.autorisation and equipier.autorisation_valide == None)]) > 0
    def verifier2(self):
        return self.verifier() and u"""<img alt="None" src="/static/admin/img/icon-yes.gif">""" or u''
    verifier2.allow_tags = True
    verifier2.short_description = 'V'

    def paiement_complet(self):
        return self.paiement >= self.prix
    def paiement_complet2(self):
        return self.paiement >= self.prix and u"""<img alt="None" src="/static/admin/img/icon-yes.gif">""" or u"""<img alt="None" src="/static/admin/img/icon-no.gif">"""
    paiement_complet2.allow_tags = True
    paiement_complet2.short_description = '€'
    
    def nombre2(self):
        return self.nombre
    nombre2.short_description = u'☺'

    def dossier_complet2(self):
        return self.dossier_complet and u"""<img alt="None" src="/static/admin/img/icon-yes.gif">""" or u"""<img alt="None" src="/static/admin/img/icon-no.gif">"""
    dossier_complet2.allow_tags = True
    dossier_complet2.short_description = mark_safe(u"""<img alt="None" src="/static/admin/img/icon-yes.gif">""")

    def dossier_complet_auto(self):
        if len([equipier for equipier in self.equipier_set.all()
                    if (not equipier.piece_jointe_valide) or
                    (equipier.age() < 18 and not equipier.autorisation_valide)]) == 0:
            return True
        if len([equipier for equipier in self.equipier_set.all()
                    if equipier.piece_jointe_valide == False or
                    (equipier.age() < 18 and equipier.autorisation_valide == False)]) > 0:
            return False
        return None
    def dossier_complet_auto2(self):
        auto = self.dossier_complet_auto()
        if auto:
            return u"""<img alt="None" src="/static/admin/img/icon-yes.gif">"""
        if auto == False:
            return u"""<img alt="None" src="/static/admin/img/icon-no.gif">"""
        return u""
    dossier_complet_auto2.allow_tags = True
    dossier_complet_auto2.short_description = mark_safe(u"""<img alt="None" src="/static/admin/img/icon-yes.gif">""")



    def frais_paypal(self):
        return ( self.prix + Decimal('0.25') ) / ( Decimal('1.000') - Decimal('0.034') ) - self.prix

    def prix_paypal(self):
        return self.prix + self.frais_paypal()
        
    def save(self, *args, **kwargs):
        if self.id:
            paiement = Equipe.objects.get(id=self.id).paiement
            if paiement != self.paiement:
                ctx = { "instance": self, }
                subject = '[6h de Paris 2013] Paiement reçu'
                message = render_to_string( 'mail_paiement.html', ctx)
                msg = EmailMessage(subject, message, 'organisation@6hdeparis.fr', [ self.gerant_email ])
                msg.content_subtype = "html"
                msg.send()

                subject = '[6h de Paris 2013] Paiement reçu %s' % (self.id, )
                message = render_to_string( 'mail_paiement_admin.html', ctx)
                msg = EmailMessage(subject, message, 'organisation@6hdeparis.fr', [ 'inscriptions@6hdeparis.fr' ])
                msg.content_subtype = "html"
                msg.send()
        else:
            if not self.numero:
                self.numero = self.getNumero()

        super(Equipe, self).save(*args, **kwargs)
        if not self.gerant_ville2:
            self.gerant_ville2 = lookup_ville(self.gerant_ville, self.gerant_code_postal, self.gerant_pays)
            super(Equipe, self).save()

    def send_mail_relance(self, mail=None):
        #if self.paiement_complet and self.dossier_complet_auto:
        #    return
        ctx = { "instance": self, }
        subject = '[6h de Paris 2013] Votre inscription / Your registration'
        message = render_to_string( 'mail_relance.html', ctx)
        msg = EmailMessage(subject, message, 'organisation@6hdeparis.fr', [ mail or self.gerant_email ])
        msg.content_subtype = "html"
        msg.send()

    def send_mail_erreur(self, message='', mail=None):
        #if self.paiement_complet and self.dossier_complet_auto:
        #    return
        ctx = { "instance": self, 'message': message }
        subject = '[6h de Paris 2013] Votre inscription / Your registration'
        message = render_to_string( 'mail_erreur.html', ctx)
        msg = EmailMessage(subject, message, 'organisation@6hdeparis.fr', [ mail or self.gerant_email ])
        msg.content_subtype = "html"
        msg.send()

    def getNumero(self):
        if self.numero:
            return self.numero
        if self.categorie.startswith('ID'):
            m = Equipe.objects.filter(categorie__startswith='ID').aggregate(models.Max('numero'))['numero__max']
        elif self.categorie.startswith('DU'):
            m = Equipe.objects.filter(categorie__startswith='DU').aggregate(models.Max('numero'))['numero__max']
            if not m:
                m = 10
        else:
            m = Equipe.objects.exclude(categorie__startswith='ID').exclude(categorie__startswith='DU').aggregate(models.Max('numero'))['numero__max']
            if not m:
                m = 100
        return m + 1

class Equipier(models.Model):
    numero            = models.IntegerField(_(u'Numéro'))
    equipe            = models.ForeignKey(Equipe)
    nom               = models.CharField(_(u'Nom'), max_length=200)
    prenom            = models.CharField(_(u'Prénom'), max_length=200, blank=True)
    sexe              = models.CharField(_(u'Sexe'), max_length=1, choices=SEXE_CHOICES)
    adresse1          = models.CharField(_(u'Adresse'), max_length=200, blank=True)
    adresse2          = models.CharField(_(u'Adresse'), max_length=200, blank=True)
    ville             = models.CharField(max_length=200)
    code_postal       = models.CharField(max_length=200)
    pays              = CountryField(_(u'Pays'), default='FR')
    email             = models.EmailField(_(u'e-mail'), max_length=200, blank=True)
    date_de_naissance = models.DateField(_(u'Date de naissance'))
    autorisation      = models.FileField(_(u'Autorisation parentale'), upload_to='certificats', blank=True)
    autorisation_valide  = models.NullBooleanField(_(u'Autorisation parentale valide'))
    justificatif      = models.CharField(_(u'Justificatif'), max_length=15, choices=JUSTIFICATIF_CHOICES)
    num_licence       = models.CharField(_(u'Numéro de licence'), max_length=15, blank=True)
    piece_jointe      = models.FileField(_(u'Certificat ou licence'), upload_to='certificats', blank=True)
    piece_jointe_valide  = models.NullBooleanField(_(u'Certificat ou licence valide'))
    parent            = models.CharField(_(u'Lien de parenté'), max_length=200, blank=True)
    piece_jointe2       = models.FileField(_(u'Justificatif entreprise / etudiant'), upload_to='certificats', blank=True)
    piece_jointe2_valide  = models.NullBooleanField(_(u'Justificatif valide'))
    ville2            = models.ForeignKey(Ville, null=True)
    
    def age(self):
        today = date(YEAR, MONTH, DAY)
        try: 
            birthday = self.date_de_naissance.replace(year=today.year)
        except ValueError: # raised when birth date is February 29 and the current year is not a leap year
            birthday = self.date_de_naissance.replace(year=today.year, day=self.date_de_naissance.day-1)
        return today.year - self.date_de_naissance.year - (birthday > today)

    def __unicode__(self):
        return u'%d' % self.numero

    def save(self, *args, **kwargs):
        super(Equipier, self).save(*args, **kwargs)
        if not self.ville2:
            self.ville2 = lookup_ville(self.ville, self.code_postal, self.pays)
            super(Equipier, self).save()

    def dossard(self):
        if self.equipe.categorie.startswith('ID'):
            return self.equipe.numero
        return self.equipe.numero * 10 + self.numero




