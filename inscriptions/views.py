# -*- coding: utf-8 -*-
import sys
from models import Equipe, Equipier, Ville, SEXE_CHOICES, JUSTIFICATIF_CHOICES
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError, Http404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.forms import ModelForm, Form, CharField, PasswordInput, HiddenInput, Select, RadioSelect
from django.forms.extras.widgets import SelectDateWidget
from django.forms.formsets import formset_factory
from django.forms.models import BaseModelFormSet
from django.utils.translation import ugettext as _
from django.core.mail import EmailMessage
from django.utils.http import urlencode
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import urllib2
import random
from settings import *
from datetime import datetime
from django.utils import timezone
from threading import Thread
import imaplib, csv, re, cStringIO

class EquipeForm(ModelForm):
    class Meta:
        model = Equipe
        exclude = ('paiement', 'dossier_complet', 'password', 'date', 'commentaires', 'paiement_info', 'gerant_ville2', 'numero')
        widgets = {
            #'password': PasswordInput(),
            'categorie': HiddenInput(),
            'prix': HiddenInput(),
            'nombre': Select(choices=tuple([(i, i) for i in range(1, 6)])),
        }

class EquipierForm(ModelForm):
    class Meta:
        model = Equipier
        exclude = ('equipe', 'numero', 'piece_jointe_valide', 'autorisation_valide', 'piece_jointe2_valide', 'ville2', 'code_eoskates')
        widgets = {
            'sexe':              Select(choices=SEXE_CHOICES),
            'date_de_naissance': SelectDateWidget(years=range(YEAR-MIN_AGE, YEAR-100, -1)),
            'justificatif':      RadioSelect(choices=JUSTIFICATIF_CHOICES),
        }

EquipierFormset = formset_factory(EquipierForm, formset=BaseModelFormSet, extra=5)
EquipierFormset.model = Equipier

class mailThread(Thread):
    def __init__ (self,msg):
        Thread.__init__(self)
        self.msg = msg

    def run(self):  
        self.msg.send()

def form(request, id=None, code=None):
    instance = None
    old_password = None
    equipier_count = Equipier.objects.count()
    if id:
        instance = get_object_or_404(Equipe, id=id)
        old_password = instance.password
        #if 'password' not in request.session or instance.password != request.session['password']:
        #    return render_to_response('login.html', RequestContext(request, {
        #        "form": LoginForm(),
        #        "instance": instance,
        #    }))
        if instance.password != code:
            raise Http404()
    if request.method == 'POST':
        equipe_form = EquipeForm(request.POST, request.FILES, instance=instance)
        if instance:
            equipier_formset = EquipierFormset(request.POST, request.FILES, queryset=instance.equipier_set.all())
        else:
            if datetime.now() >= datetime(CLOSE_YEAR, CLOSE_MONTH, CLOSE_DAY) or equipier_count >= MAX_EQUIPIER:
                return redirect('/')
            equipier_formset = EquipierFormset(request.POST, request.FILES)
        if equipe_form.is_valid() and equipier_formset.is_valid():
            new_instance = equipe_form.save(commit=False)
            new_instance.password = old_password
            if not instance:
                new_instance.password = '%06x' % random.randrange(0x100000, 0xffffff)
            #if instance and instance.categorie == new_instance.categorie and instance.prix:
            #    new_instance.prix = instance.prix
            #else:
            #    new_instance.prix = CATEGORIES[new_instance.categorie]['prix']
            new_instance.save()
            for i in range(0, new_instance.nombre):
                equipier_instance = equipier_formset.forms[i].save(commit=False)
                equipier_instance.numero = i + 1
                equipier_instance.equipe = new_instance
                equipier_instance.save()
            ctx = RequestContext(request, {
                "instance": new_instance,
                "url": request.build_absolute_uri(reverse(
                    'inscriptions.edit', kwargs={
                        'id': new_instance.id,
                        'code': new_instance.password
                    }
                )),
                "url2": request.build_absolute_uri(reverse(
                    'inscriptions.done', kwargs={
                        'id': new_instance.id,
                    }
                )),
                'url_admin': request.build_absolute_uri(reverse( 
                    'admin:inscriptions_equipe_change', 
                    args=[new_instance.id]
                )),
                "equipe_form": equipe_form,
                "equipier_formset": equipier_formset,
            })
            if not instance:
                subject = '[6h de Paris 2013] Inscription'
                message = render_to_string( 'mail_inscription.html', ctx)
                msg = EmailMessage(subject, message, 'organisation@6hdeparis.fr', [ new_instance.gerant_email ])
                msg.content_subtype = "html"
                mailThread(msg).start()

                subject = '[6h de Paris 2013] Inscription %s' % (new_instance.id, )
                message = render_to_string( 'mail_inscription_admin.html', ctx)
                msg = EmailMessage(subject, message, 'organisation@6hdeparis.fr', [ 'inscriptions@6hdeparis.fr' ])
                msg.content_subtype = "html"
                mailThread(msg).start()
            return redirect('inscriptions.done', id=new_instance.id)
    else:
        equipe_form = EquipeForm(instance=instance)
        if instance:
            equipier_formset = EquipierFormset(queryset=instance.equipier_set.all())
        else:
            equipier_formset = EquipierFormset(queryset=Equipier.objects.none())
    date_prix2 = timezone.make_aware(datetime(2013, 6, 17), timezone.get_default_timezone())
    return render_to_response("form.html", RequestContext(request, {
        "equipe_form": equipe_form,
        "equipier_formset": equipier_formset,
        "instance": instance,
        "create": not instance,
        "update": not not instance,
        "solo": Equipe.objects.filter(categorie__startswith='ID').count(),
        "max_solo": datetime(2013, 6, 8) <= datetime.now() and 49 or 30,
        "equipier_count": equipier_count,
        "prix2": date_prix2 <= timezone.now() and (not instance or instance.date >= date_prix2)
    }))

def done(request, id):
    instance = get_object_or_404(Equipe, id=id)
    ctx = RequestContext(request, {
        "instance": instance,
        "url": request.build_absolute_uri(reverse(
            'inscriptions.edit', kwargs={
                'id': instance.id,
                'code': instance.password
            }
        )),
        "paypal_ipn_url": request.build_absolute_uri(reverse('inscriptions.ipn')),
        "hour": datetime.now().strftime('%H%M'),
    })
    return render_to_response('done.html', ctx)

@csrf_exempt
def ipn(request):
    """PayPal IPN (Instant Payment Notification)
    Cornfirms that payment has been completed and marks invoice as paid.
    Adapted from IPN cgi script provided at http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/456361"""

    print >>sys.stderr, 1
    try:
        if not confirm_ipn_data(request.body, PAYPAL_URL):
            return HttpResponse()

        data = request.POST
        if not 'payment_status' in data or not data['payment_status'] == "Completed":
            # We want to respond to anything that isn't a payment - but we won't insert into our database.
             return HttpResponse()

        equipe = get_object_or_404(Equipe, id=data['invoice'][0:-4])
        equipe.paiement = data['mc_gross']
        equipe.paiement_info = 'Paypal %s %s' % (datetime.now(), data['txn_id'])
        equipe.save()

    except Exception, e:
        print >>sys.stderr, e

    return HttpResponse()

def confirm_ipn_data(data, PP_URL):
    # data is the form data that was submitted to the IPN URL.
    print >>sys.stderr, 2
    #PP_URL = 'https://www.paypal.com/cgi-bin/webscr'

    print >>sys.stderr, 3, PP_URL
    params = data + '&' + urlencode({ 'cmd': "_notify-validate" })

    print >>sys.stderr, 4, params
    req = urllib2.Request(PP_URL)
    req.add_header("Content-type", "application/x-www-form-urlencoded")
    fo = urllib2.urlopen(req, params)

    ret = fo.read()
    print >>sys.stderr, 5, ret
    if ret == "VERIFIED":
        print >>sys.stderr, "PayPal IPN data verification was successful."
    else:
        print >>sys.stderr, "PayPal IPN data verification failed."
        return False

    return True

@csrf_exempt
def check_name(request):
    return HttpResponse(Equipe.objects.filter(nom__iexact=request.POST['nom']).exclude(id=request.POST['id']).count(), content_type="text/plain")

def list(request):
    return render_to_response('list.html', RequestContext(request, {
       'object_list': Equipe.objects.all(),
       'villes': Ville.objects.all().order_by('nom').annotate(equipiers=Count('equipier')),
       'equipiers': Equipier.objects.all(),
    }))

@login_required
def send_mail(request, id, template='mail_relance.html'):
    instance = get_object_or_404(Equipe, id=id)

    if request.method == 'POST':
        msg = EmailMessage(request.POST['subject'], request.POST['message'], request.POST['sender'], [ request.POST['mail'] ])
        msg.content_subtype = "html"
        msg.send()
        messages.add_message(request, messages.INFO, u'Message envoyé à %s' % (request.POST['mail'], ))
        return redirect('/admin/inscriptions/equipe/%s/' % (instance.id, ))

    message = render_to_string(template or 'mail_relance.html', { "instance": instance, })

    return render_to_response('send_mail.html', RequestContext(request, {
        'message': message,
        'sender': 'organisation@6hdeparis.fr',
        'mail': instance.gerant_email,
        'subject': '[6h de Paris 2013] Votre inscription / Your registration'
    }))

@login_required
def bene(request):
    server = 'localhost'
    login  = ''
    passwd = ''

    c = imaplib.IMAP4(server)
    c.login(login, passwd)

    data={}
    out = cStringIO.StringIO()
    o=csv.writer(out)
    # Archive INBOX
    c.select()
    code, (list,) = c.search(None, 'ALL')
    for i in list.split():
        try:
            msg = c.fetch(i, '(RFC822)')[1][0][1]
            if type(msg) == tuple:
                msg = ''.join(msg)
            msg = "\r\n".join(msg.split("\r\n\r\n")[1:])
            row = [':' in i and i.split(': ')[1] or i for i in msg.split("\r\n")]
            row[4] = re.sub('([0-9]{2})', '\\1 ', ''.join(row[4].split(' ')))
            o.writerow(row)
        except:
            pass
    c.close()
    r = HttpResponse(out.getvalue(), mimetype='text/csv')
    out.close()
    return r

@login_required
def dossards(request):
    return render_to_response('dossards.html', RequestContext(request, {
        'equipiers': Equipier.objects.all()
    }))

def equipiers(request):
    return render_to_response('equipiers.html', RequestContext(request, {
        'equipiers': Equipier.objects.all()
    }))

#@login_required
def dossardsCSV(request):
    code = request.GET.get('code', 'utf-8')
    out = cStringIO.StringIO()
    o=csv.writer(out)
    o.writerow([
        'inscription',
        'equipe',
        'nom',
        'categorie',
        'dossard',
        'nom',
        'prenom',
        'sexe',
        'date_de_naissance',
        'num_licence',
        'gerant_nom',
        'gerant_prenom',
        'gerant_ville',
        'gerant_code_postal',
        'gerant_code_pays',
    ])
    for e in Equipier.objects.all():
        row = [
            e.equipe.id,
            e.equipe.numero,
            e.equipe.nom,
            e.equipe.categorie,
            e.dossard(),
            e.nom,
            e.prenom,
            e.sexe,
            e.date_de_naissance,
            e.num_licence,
            e.equipe.gerant_nom,
            e.equipe.gerant_prenom,
            e.equipe.gerant_ville,
            e.equipe.gerant_code_postal,
            e.equipe.gerant_pays,
        ]
        row = [ type(i) == unicode and i.encode(code) or i for i in row ]
        o.writerow(row)

    r = HttpResponse(out.getvalue(), mimetype='text/csv')
    out.close()
    return r

def dossardsEquipesCSV(request):
    code = request.GET.get('code', 'utf-8')
    out = cStringIO.StringIO()
    o=csv.writer(out)
    o.writerow([
        'inscription',
        'equipe',
        'nom',
        'categorie',
        'gerant_nom',
        'gerant_prenom',
        'gerant_ville',
        'gerant_code_postal',
        'gerant_code_pays',
    ])
    for e in Equipe.objects.all():
        row = [
            e.id,
            e.numero,
            e.nom,
            e.categorie,
            e.gerant_nom,
            e.gerant_prenom,
            e.gerant_ville,
            e.gerant_code_postal,
            e.gerant_pays,
        ]
        row = [ type(i) == unicode and i.encode(code) or i for i in row ]
        o.writerow(row)

    r = HttpResponse(out.getvalue(), mimetype='text/csv')
    out.close()
    return r

def dossardsEquipiersCSV(request):
    code = request.GET.get('code', 'utf-8')
    out = cStringIO.StringIO()
    o=csv.writer(out)
    o.writerow([
        'equipe',
        'dossard',
        'nom',
        'prenom',
        'sexe',
        'date_de_naissance',
        'num_licence',
    ])
    for e in Equipier.objects.all():
        row = [
            e.equipe.numero,
            e.dossard(),
            e.nom,
            e.prenom,
            e.sexe,
            e.date_de_naissance,
            e.num_licence,
        ]
        row = [ type(i) == unicode and i.encode(code) or i for i in row ]
        o.writerow(row)

    r = HttpResponse(out.getvalue(), mimetype='text/csv')
    out.close()
    return r

