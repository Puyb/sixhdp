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
from django.contrib.auth.models import User


SEXE_CHOICES = (
    ('H', _(u'Homme')),
    ('F', _(u'Femme')),
)

MIXITE_CHOICES = (
    ('H', _(u'Homme')),
    ('F', _(u'Femme')),
    ('MX', _(u'Homme ou Mixte')),
    ('FX', _(u'Femme ou Mixte')),
    ('X', _(u'Mixte')),
)

JUSTIFICATIF_CHOICES = (
    ('licence',    _(u'Licence FFRS 2013')),
    ('certificat', _(u'Certificat médical établi après le 4/08/2012')),
)

ROLE_CHOICES = (
    ('admin', _(u'Administrateur')),
    ('organisateur', _(u'Organisateur')),
    ('validateur', _(u'Validateur')),
)

CONNU_CHOICES = (
    (u'Roller en LIgne', _(u'Roller en Ligne')),
    (u'Facebook', _('Facebook')),
    (u'Presse', _(u'Presse')),
    (u'Bouche à oreille', _(u'Bouche à oreille')),
    (u'Flyer pendant une course', _(u'Fley pendant une course')),
    (u'Flyer pendant une randonnée', _(u'Flyer pendant une randonnée')),
    (u'Affiche', _(u'Affiche')),
    (u'Informations de la Mairie de Paris', _(u'Information de la Maire de Paris')),
)

TAILLES_CHOICES = (
    ('XS', _('XS')),
    ('S', _('S')),
    ('M', _('M')),
    ('L', _('L')),
    ('XL', _('XL')),
    ('XXL', _('XXL')),
)

#class Chalenge(model.Model):
#    nom = models.CharField(_('Nom'), max=200)

class Course(models.Model):
    nom                 = models.CharField(_(u'Nom'), max_length=200)
    uid                 = models.CharField(_(u'uid'), max_length=200)
    ville               = models.CharField(_(u'Ville'), max_length=200)
#    challenge           = models.ForeignKey(Challenge, blank=True, null=True)
    date                = models.DateField(_(u'Date'))
    date_ouverture      = models.DateField(_(u"Date d'ouverture des inscriptionss"))
    date_augmentation   = models.DateField(_(u"Date d'augmentation dss tarifs"))
    date_fermeture      = models.DateField(_(u"Date de fermeture des inscriptions"))
    limite_participants = models.DecimalField(_(u"Limite du nombre de participants"), max_digits=6, decimal_places=0)
    limite_solo         = models.DecimalField(_(u"Limite du nombre de solo"), max_digits=6, decimal_places=0)
    paypal              = models.EmailField(_(u'Adresse paypal'))
    ordre               = models.CharField(_(u'Ordre des chèques'), max_length=200)
    adresse             = models.TextField(_(u'Adresse'), blank=True)
    url                 = models.URLField(_(u'URL'))
    url_reglement       = models.URLField(_(u'URL Réglement'))
    email_contact       = models.EmailField(_(u'Email contact'))

    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = self.nom.lower().replace(' ', '_')
        super(Course, self).save(*args, **kwargs)

    def __unicode__(self):
        return '%s (%s)' % (self.nom, self.date)

class Categorie(models.Model):
    course          = models.ForeignKey(Course, related_name='categories')
    nom             = models.CharField(_(u'Nom'), max_length=200)
    code            = models.CharField(_(u'Code'), max_length=10)
    prix1           = models.DecimalField(_(u"Prix normal"), max_digits=7, decimal_places=2)
    prix2           = models.DecimalField(_(u"Prix augmenté"), max_digits=7, decimal_places=2)
    min_equipiers   = models.IntegerField(_(u"Nombre minimum d'équipiers"))
    max_equipiers   = models.IntegerField(_(u"Nombre maximum d'équipiers"))
    min_age         = models.IntegerField(_(u'Age minimum'), default=12)
    sexe            = models.CharField(_(u'Sexe'), max_length=2, choices=MIXITE_CHOICES)
    validation      = models.TextField(_(u'Validation function (javascript)'))
    numero_dossard  = models.IntegerField(_(u'Numero de dossard (début)'), default=0)

    def __unicode__(self):
        return '%s (%s)' % (self.nom, self.code)

class Ville(models.Model):
    lat      = models.DecimalField(max_digits=10, decimal_places=7)
    lng      = models.DecimalField(max_digits=10, decimal_places=7)
    nom      = models.CharField(max_length=200)
    region   = models.CharField(max_length=200)
    pays     = models.CharField(max_length=200)
    response = models.CharField(max_length=65535)

def lookup_ville(nom, cp, pays):
    nom = nom.lower()
    nom = re.sub('[- ,/]+', ' ', nom)
    try:
        return Ville.objects.get(nom=nom)
    except (Ville.DoesNotExist, e):
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
    except (Ville.DoesNotExist, e):
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
    categorie          = models.ForeignKey(Categorie)
    course             = models.ForeignKey(Course)
    nombre             = models.IntegerField(_(u"Nombre d'équipiers"))
    paiement_info      = models.CharField(_(u'Détails'), max_length=200, blank=True)
    prix               = models.DecimalField(_(u'Prix'), max_digits=5, decimal_places=2)
    paiement           = models.DecimalField(_(u'Paiement reçu'), max_digits=5, decimal_places=2, null=True, blank=True)
    dossier_complet    = models.NullBooleanField(_(u'Dossier complet'))
    date               = models.DateTimeField(_(u"Date d'insciption"), auto_now_add=True)
    commentaires       = models.TextField(_(u'Commentaires'), blank=True)
    gerant_ville2      = models.ForeignKey(Ville, null=True)
    numero             = models.IntegerField(_(u'Numéro'))
    connu              = models.CharField(_('Comment avez vous connu la course ?'), max_length=200, choices=CONNU_CHOICES)

    def __unicode__(self):
        return u'%s - %s - %s' % (self.id, self.categorie, self.nom)

    def licence_manquantes(self):
        return [equipier for equipier in self.equipier_set.all() if equipier.justificatif == 'licence' and not equipier.piece_jointe_valide and not equipier.piece_jointe ]

    def certificat_manquantes(self):
        return [equipier for equipier in self.equipier_set.all() if equipier.justificatif == 'certificat' and not equipier.piece_jointe_valide and not equipier.piece_jointe ]

    def autorisation_manquantes(self):
        return [equipier for equipier in self.equipier_set.all() if equipier.age() < 18 and not equipier.autorisation_valide and not equipier.autorisation ]

    def verifier(self):
        return len([equipier for equipier in self.equipier_set.all() 
                if (equipier.piece_jointe and equipier.piece_jointe_valide == None) or
                   (equipier.autorisation and equipier.autorisation_valide == None)]) > 0
    def paiement_complet(self):
        return self.paiement >= self.prix
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
                msg = EmailMessage(subject, message, self.course.email_contact, [ self.gerant_email ])
                msg.content_subtype = "html"
                msg.send()

                subject = '[6h de Paris 2013] Paiement reçu %s' % (self.id, )
                message = render_to_string( 'mail_paiement_admin.html', ctx)
                msg = EmailMessage(subject, message, self.course.email_contact, [ self.course.email_contact ])
                msg.content_subtype = "html"
                msg.send()
        else:
            if not self.numero:
                self.numero = self.getNumero()

        super(Equipe, self).save(*args, **kwargs)
        if not self.gerant_ville2:
            self.gerant_ville2 = lookup_ville(self.gerant_ville, self.gerant_code_postal, self.gerant_pays)
            super(Equipe, self).save()

    def send_mail(self, template, mail=None):
        #if self.paiement_complet and self.dossier_complet_auto:
        #    return
        mail = Template_mail.objects.get(id=template)
        ctx = { "instance": self, }
        subject = Template(mail.sujet).render(ctx)
        message = Template(mail.message).render(ctx)
        msg = EmailMessage(subject, message, self.course.email_contact, [ mail or self.gerant_email ])
        msg.content_subtype = "html"
        msg.send()

    def getNumero(self):
        if self.numero:
            return self.numero
        if self.categorie.startswith('ID'):
            m = Equipe.objects.filter(categorie__startswith='ID').aggregate(models.Max('numero'))['numero__max']
            if not m:
                m = 200
        elif self.categorie.startswith('DU'):
            m = Equipe.objects.filter(categorie__startswith='DU').aggregate(models.Max('numero'))['numero__max']
            if not m:
                m = 300
        elif self.categorie.startswith('HND'):
            m = Equipe.objects.filter(categorie__startswith='HND').aggregate(models.Max('numero'))['numero__max']
            if not m:
                m = 400
        else:
            m = Equipe.objects.exclude(categorie__startswith='ID').exclude(categorie__startswith='DU').exclude(categorie__startswith='HND').aggregate(models.Max('numero'))['numero__max']
            if not m:
                m = 0
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
    ville_normalisee  = models.ForeignKey(Ville, null=True)
    code_eoskates     = models.CharField(_(u'Code EOSkates'), max_length=20, blank=True)
    transpondeur      = models.CharField(_(u'Transpondeur'), max_length=20, blank=True)
    taille_tshirt     = models.CharField(_(u'Taille T-shirt'), max_length=3, choices=TAILLES_CHOICES)
    
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
        if not self.ville_normalisee:
            self.ville_normalisee = lookup_ville(self.ville, self.code_postal, self.pays)
            super(Equipier, self).save()

    def dossard(self):
        return self.equipe.numero * 10 + self.numero

    def send_mail(self, subject='', template=None, mail=None):
        ctx = { "equipier": self, }
        subject = subject
        message = render_to_string(template, ctx)
        msg = EmailMessage(subject, message, self.equipe.course.email_contact, [ mail or self.email ])
        msg.content_subtype = "html"
        msg.send()


class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    course = models.ManyToManyField(Course, related_name='+')
    role = models.CharField(_("Role"), max_length=20, choices=ROLE_CHOICES)

User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])

class TemplateMail(models.Model):
    course = models.ForeignKey(Course)
    sujet = models.CharField(_('Sujet'), max_length=200)
    message = models.TextField(_('Message'))

