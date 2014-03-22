# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django_countries import CountryField
from django.conf import settings
from django.template.loader import render_to_string
from django.template import Template, Context
from django.core.mail import EmailMessage
import os, re, urllib, simplejson
from django.db import models
from settings import *
from datetime import date
from decimal import Decimal
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from django.db.models import Min, Max, Count, Avg
from utils import iriToUri, MailThread
import traceback


SEXE_CHOICES = (
    ('H', _(u'Homme')),
    ('F', _(u'Femme')),
)

MIXITE_CHOICES = (
    ('H', _(u'Homme')),
    ('F', _(u'Femme')),
    ('HX', _(u'Homme ou Mixte')),
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

DESTINATAIRE_CHOICES = (
    ('Equipe', _(u"Gerant d'équipe")),
    ('Equipier', _(u'Equipier')),
    ('Organisateur', _(u'Organisateur')),
    ('Tous', _(u'Tous')),
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

    @property
    def ouverte(self):
        return self.date_ouverture <= date.today()

    @property
    def fermee(self):
        return self.date_fermeture < date.today()

    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = self.nom.lower().replace(' ', '_')
        super(Course, self).save(*args, **kwargs)

    def __unicode__(self):
        return '%s (%s)' % (self.nom, self.date)

    def send_mail(self, nom, instances):
        mail = TemplateMail.objects.get(course=self, nom=nom)
        mail.send(instances)

    def stats(self):
        model_stats = {
            "equipes": 0,
            "equipiers": 0,
            "hommes": 0,
            "femmes": 0,
            "paiement": 0,
            "prix": 0,
            "nbcertifenattente": 0,
            "pc": 0,
            "pi": 0,
            "pe": 0,
            "pv": 0,
            "ipc": 0,
            "ipi": 0,
            "ipe": 0,
            "ipv": 0,
        }
        result = {
            "categories": {},
            "jours": {},
            "villes": {},
            "regions": {},
            "pays": {},
            "course": {},
        }

        equipes = (Equipe.objects.filter(course=self)
            .annotate(equipiers_count=Count('equipier'))
            .select_related('categorie', 'gerant_ville2')
            .prefetch_related('equipier_set')
        )
        for equipe in equipes:
        #for equipe in Equipe.objects.raw("""
        #        SELECT inscriptions_equipe.*, count(e1.id) as equipiers_count, count(e2.id) as hommes_count, count(e3.id) as femmes_count
        #            FROM inscriptions_equipe
        #            LEFT JOIN inscriptions_equipier e1 ON inscriptions_equipe.id = e1.equipe_id
        #            LEFT JOIN inscriptions_equipier e2 ON inscriptions_equipe.id = e2.equipe_id AND e2.sexe = 'H'
        #            LEFT JOIN inscriptions_equipier e3 ON inscriptions_equipe.id = e3.equipe_id AND e3.sexe = 'F'
        #            WHERE course_id=%s GROUP BY inscriptions_equipe.id""", [ self.id ]).prefetch_selected('equipiers'):
            stats = model_stats.copy()
            keys = {
                "categories": equipe.categorie_id and equipe.categorie.code or '',
                "jours": (equipe.date.date() - self.date_ouverture).days,
                "villes":  equipe.gerant_ville2_id and (equipe.gerant_ville2.pays == 'France' and equipe.gerant_ville2.nom    or equipe.gerant_ville2.pays) or '',
                "regions": equipe.gerant_ville2_id and (equipe.gerant_ville2.pays == 'France' and equipe.gerant_ville2.region or equipe.gerant_ville2.pays) or '',
                "pays":    equipe.gerant_ville2_id and equipe.gerant_ville2.pays or '',
            }
                    
            stats['equipes'] = 1
            stats['equipiers'] = equipe.equipiers_count
            #stats['hommes'] = equipe.hommes_count
            #stats['femmes'] = equipe.femmes_count
            token = ''
            if not equipe.paiement_complet():
                token += 'i'
            token += 'p';
            if equipe.verifier():
                token += 'v'
            else:
                if equipe.dossier_complet_auto() == True:
                    token += 'c'
                elif equipe.dossier_complet_auto() == False:
                    token += "e"
                else:
                    token += "i"
            stats[token] = 1

            stats['paiement'] = float(equipe.paiement or 0)
            stats['prix'] = float(equipe.prix)
            #stats['nbcertifenattente'] = len(equipe.licence_manquantes()) + len(equipe.certificat_manquantes()) + len(equipe.autorisation_manquantes())


            for key, index in keys.items():
                if index not in result[key]:
                    result[key][index] = model_stats.copy();
                for stat, value in stats.items():
                    result[key][index][stat] += value

        return result

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
    numero_debut    = models.IntegerField(_(u'Numero de dossard (début)'), default=0)
    numero_fin      = models.IntegerField(_(u'Numero de dossard (fin)'), default=0)

    def __unicode__(self):
        return self.code

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
    except Ville.DoesNotExist, e:
        pass

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

    class Meta:
        unique_together = ( ('course', 'numero'), )

    def __unicode__(self):
        return u'%s - %s - %s' % (self.id, self.categorie, self.nom)

    def licence_manquantes(self):
        return [equipier for equipier in self.equipier_set.all() if equipier.justificatif == 'licence' and not equipier.piece_jointe_valide and not equipier.piece_jointe ]

    def certificat_manquantes(self):
        return [equipier for equipier in self.equipier_set.all() if equipier.justificatif == 'certificat' and not equipier.piece_jointe_valide and not equipier.piece_jointe ]

    def autorisation_manquantes(self):
        return [equipier for equipier in self.equipier_set.all() if equipier.age() < 18 and not equipier.autorisation_valide and not equipier.autorisation ]

    def verifier(self):
        return len([equipier for equipier in self.equipier_set.all() if equipier.verifer]) > 0
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
                try:
                    self.send_mail('paiement')
                except e:
                    traceback.print_exc(e)
                try:
                    self.send_mail('paiement_admin')
                except e:
                    traceback.print_exc(e)
        else:
            if not self.numero:
                self.numero = self.getNumero()

        super(Equipe, self).save(*args, **kwargs)
        if not self.gerant_ville2:
            self.gerant_ville2 = lookup_ville(self.gerant_ville, self.gerant_code_postal, self.gerant_pays)
            super(Equipe, self).save()

    def send_mail(self, nom):
        self.course.send_mail(nom, [self])

    def getNumero(self):
        if self.numero:
            return self.numero
        start = self.categorie.numero_debut
        end = self.categorie.numero_fin

        res = Equipe.objects.raw("""SELECT e1.id as id, e1.numero as numero FROM inscriptions_equipe e1 
                LEFT JOIN inscriptions_equipe e2 ON e1.numero=e2.numero-1 AND e1.course_id=e2.course_id
                WHERE e1.course_id=%s AND e1.numero>=%s AND e1.numero<=%s AND e2.numero IS NULL LIMIT 1""", 
                [self.course.id, start, end])

        if len(list(res)) == 0 or res[0].numero == None:
            numero = start
        else:
            numero = res[0].numero + 1
        return numero

class EquipierManager(models.Manager):
    def get_query_set(self):
        return super(EquipierManager, self).get_query_set().extra(select={
            "verifier": "((piece_jointe AND piece_jointe_valide IS NULL) OR (autorisation AND autorisation_valide IS NULL))",
        })

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
    code_eoskates     = models.CharField(_(u'Code EOSkates'), max_length=20, blank=True)
    transpondeur      = models.CharField(_(u'Transpondeur'), max_length=20, blank=True)
    taille_tshirt     = models.CharField(_(u'Taille T-shirt'), max_length=3, choices=TAILLES_CHOICES, blank=True)
    
    def age(self):
        today = self.equipe.course.date
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
        return self.equipe.numero * 10 + self.numero

    def send_mail(self, nom):
        self.course.send_mail(nom, [self])

    objects = EquipierManager()

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    course = models.ManyToManyField(Course, related_name='+')
    role = models.CharField(_("Role"), max_length=20, choices=ROLE_CHOICES)

User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])

class TemplateMail(models.Model):
    course = models.ForeignKey(Course)
    nom = models.CharField(_('Nom'), max_length=200)
    destinataire = models.CharField(_('Destinataire'), max_length=20, choices=DESTINATAIRE_CHOICES)
    bcc = models.CharField(_(u'Copie cachée à'), max_length=1000, blank=True)
    sujet = models.CharField(_('Sujet'), max_length=200)
    message = models.TextField(_('Message'))
    class Meta:
        unique_together= ( ('course', 'nom'), )

    def send(self, instances):
        messages = []
        for instance in instances:
            context = Context({ "instance": instance, })
            subject = Template(self.sujet).render(context)
            message = Template(self.message).render(context)

            dest = self.course.email_contact
            if isinstance(instance, Equipe):
                dest = instance.gerant_email
            if isinstance(instance, Equipier):
                dest = instance.email
            
            bcc = []
            if self.bcc:
                bcc = re.split('[,; ]+', self.bcc)
            
            message = EmailMessage(subject, message, self.course.email_contact, [ dest ], bcc)
            message.content_subtype = "html"
            messages.append(message)
        MailThread(messages).start()
