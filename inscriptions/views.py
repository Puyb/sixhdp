import sys
from models import Equipe, Equipier, SEXE_CHOICES, JUSTIFICATIF_CHOICES
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
import urllib2
import random
from settings import *
from datetime import datetime

class EquipeForm(ModelForm):
    class Meta:
        model = Equipe
        exclude = ('paiement', 'dossier_complet', 'password', 'date', 'commentaires', 'paiement_info', 'piece_jointe_valide')
        widgets = {
            #'password': PasswordInput(),
            'categorie': HiddenInput(),
            'prix': HiddenInput(),
            'nombre': Select(choices=tuple([(i, i) for i in range(1, 6)])),
        }

class EquipierForm(ModelForm):
    class Meta:
        model = Equipier
        exclude = ('equipe', 'numero', 'piece_jointe_valide', 'autorisation_valide')
        widgets = {
            'sexe':              Select(choices=SEXE_CHOICES),
            'date_de_naissance': SelectDateWidget(years=range(YEAR-MIN_AGE, YEAR-100, -1)),
            'justificatif':      RadioSelect(choices=JUSTIFICATIF_CHOICES),
        }

EquipierFormset = formset_factory(EquipierForm, formset=BaseModelFormSet, extra=5)
EquipierFormset.model = Equipier

def form(request, id=None, code=None):
    instance = None
    old_password = None
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
                msg.send()

                subject = '[6h de Paris 2013] Inscription %s' % (new_instance.id, )
                message = render_to_string( 'mail_inscription_admin.html', ctx)
                msg = EmailMessage(subject, message, 'organisation@6hdeparis.fr', [ 'inscriptions@6hdeparis.fr' ])
                msg.content_subtype = "html"
                msg.send()
            return redirect('inscriptions.done', id=new_instance.id)
    else:
        equipe_form = EquipeForm(instance=instance)
        if instance:
            equipier_formset = EquipierFormset(queryset=instance.equipier_set.all())
        else:
            equipier_formset = EquipierFormset(queryset=Equipier.objects.none())
    return render_to_response("form.html", RequestContext(request, {
        "equipe_form": equipe_form,
        "equipier_formset": equipier_formset,
        "instance": instance,
        "create": not instance,
        "update": not not instance,
        "solo": Equipe.objects.filter(categorie__startswith='ID').count(),
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

        equipe = get_object_or_404(Equipe, id=data['invoice'])
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
    return HttpResponse(Equipe.objects.filter(nom__iexact=request.POST['nom']).count(), content_type="text/plain")
