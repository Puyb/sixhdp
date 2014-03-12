# -*- coding: utf-8 -*-
import sys
from models import Equipe, Equipier, Categorie, Ville, Course, SEXE_CHOICES, JUSTIFICATIF_CHOICES
from decorators import open_closed
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
from django.utils.http import urlencode
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Sum
import urllib2
import random
from settings import *
from datetime import datetime, date
from django.utils import timezone

class EquipeForm(ModelForm):
    class Meta:
        model = Equipe
        exclude = ('paiement', 'dossier_complet', 'password', 'date', 'commentaires', 'paiement_info', 'gerant_ville2', 'numero', 'course')
        widgets = {
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
            'date_de_naissance': SelectDateWidget(years=range(datetime.now().year , datetime.now().year - 100, -1)),
            'justificatif':      RadioSelect(choices=JUSTIFICATIF_CHOICES),
        }

EquipierFormset = formset_factory(EquipierForm, formset=BaseModelFormSet, extra=5)
EquipierFormset.model = Equipier

@open_closed
def form(request, course_uid, numero=None, code=None):
    course = get_object_or_404(Course, uid=request.path.split('/')[1])
    instance = None
    old_password = None
    equipiers_count = Equipier.objects.filter(equipe__course=course).count()
    if numero:
        instance = get_object_or_404(Equipe, numero=numero)
        if instance.course != course:
            raise Http404()
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
            if date.today() >= course.date_fermeture or equipiers_count >= course.limite_participants:
                if not request.user.is_staff:
                    return redirect('/')
            equipier_formset = EquipierFormset(request.POST, request.FILES)

        # FIXME: change date naissance years
        # years=range(course.date.year - course.min_age, course.date.year - 120, -1)

        if equipe_form.is_valid() and equipier_formset.is_valid():
            new_instance = equipe_form.save(commit=False)
            new_instance.course = course
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
                        'course_uid': course.uid,
                        'numero': new_instance.numero,
                        'code': new_instance.password
                    }
                )),
                "url2": request.build_absolute_uri(reverse(
                    'inscriptions.done', kwargs={
                        'course_uid': course.uid,
                        'numero': new_instance.numero,
                    }
                )),
                "equipe_form": equipe_form,
                "equipier_formset": equipier_formset,
            })
            if not instance:
                try:
                    course.send_mail('inscription', instance)
                except e:
                    traceback.print_exc(e)
                try:
                    course.send_mail('inscription_admin', instance)
                except e:
                    traceback.print_exc(e)
            return redirect('inscriptions.done', course_uid=course.uid, numero=new_instance.numero)
    else:
        equipe_form = EquipeForm(instance=instance)
        if instance:
            equipier_formset = EquipierFormset(queryset=instance.equipier_set.all())
        else:
            equipier_formset = EquipierFormset(queryset=Equipier.objects.none())
    date_prix2 = timezone.make_aware(datetime(2013, 6, 17), timezone.get_default_timezone())
    if instance:
        return done(request, course_uid, instance.numero)

    nombres_par_tranche = {}
    for categorie in Categorie.objects.filter(course=course):
        key = '%d-%d' % (categorie.numero_debut, categorie.numero_fin)
        if not nombres_par_tranche.has_key(key):
            nombres_par_tranche[key] = Equipe.objects.filter(course=course, numero__gte=categorie.numero_debut, numero__lte=categorie.numero_fin).count()
    
    return render_to_response("form.html", RequestContext(request, {
        "equipe_form": equipe_form,
        "equipier_formset": equipier_formset,
        "instance": instance,
        "create": not instance,
        "update": not not instance,
        "nombres_par_tranche": nombres_par_tranche,
        "equipiers_count": equipiers_count,
    }))

@open_closed
def done(request, course_uid, numero):
    course = get_object_or_404(Course, uid=request.path.split('/')[1])
    instance = get_object_or_404(Equipe, course=course, numero=numero)
    if instance.course != course:
        raise Http404()
    ctx = RequestContext(request, {
        "instance": instance,
        "url": request.build_absolute_uri(reverse(
            'inscriptions.edit', kwargs={
                'course_uid': course.uid,
                'numero': instance.numero,
                'code': instance.password
            }
        )),
        "paypal_ipn_url": request.build_absolute_uri(reverse('inscriptions.ipn', kwargs={'course_uid': course.uid })),
        "hour": datetime.now().strftime('%H%M'),
    })
    return render_to_response('done.html', ctx)

@csrf_exempt
def ipn(request, course_uid):
    """PayPal IPN (Instant Payment Notification)
    Cornfirms that payment has been completed and marks invoice as paid.
    Adapted from IPN cgi script provided at http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/456361"""

    try:
        if not confirm_ipn_data(request.body, PAYPAL_URL):
            return HttpResponse()

        data = request.POST
        if not 'payment_status' in data or not data['payment_status'] == "Completed":
            # We want to respond to anything that isn't a payment - but we won't insert into our database.
             return HttpResponse()

        equipe = get_object_or_404(Equipe, id=data['invoice'][0:-4], course__uid=course_uid)
        equipe.paiement = data['mc_gross']
        equipe.paiement_info = 'Paypal %s %s' % (datetime.now(), data['txn_id'])
        equipe.save()

    except Exception, e:
        print >>sys.stderr, e

    return HttpResponse()

def confirm_ipn_data(data, PP_URL):
    # data is the form data that was submitted to the IPN URL.
    #PP_URL = 'https://www.paypal.com/cgi-bin/webscr'

    params = data + '&' + urlencode({ 'cmd': "_notify-validate" })

    req = urllib2.Request(PP_URL)
    req.add_header("Content-type", "application/x-www-form-urlencoded")
    fo = urllib2.urlopen(req, params)

    ret = fo.read()
    if ret == "VERIFIED":
        print >>sys.stderr, "PayPal IPN data verification was successful."
    else:
        print >>sys.stderr, "PayPal IPN data verification failed."
        return False

    return True

@csrf_exempt
def check_name(request, course_uid):
    return HttpResponse(
            Equipe.objects
                .filter(course__uid=course_uid, nom__iexact=request.POST['nom'])
                .exclude(id=request.POST['id'])
                .count(),
            content_type="text/plain")

def list(request, course_uid):
    stats = Equipe.objects.filter(course__uid=course_uid).aggregate(
        count     = Count('id'),
        prix      = Sum('prix'), 
        nbpaye    = Count('prix'), 
        paie      = Sum('paiement'), 
        club      = Count('club', distinct=True),
        villes    = Count('gerant_ville2__nom', distinct=True),
        pays      = Count('gerant_ville2__pays', distinct=True),
        equipiers = Count('equipier'),

    )
    equipes = Equipe.objects.filter(course__uid=course_uid)
    return render_to_response('list.html', RequestContext(request, {
        'stats': stats,
        'equipes': equipes
    }))

def stats(request, course_uid):
    equipes = Equipe.objects.filter(course__uid=course_uid)
    equipiers = Equipier.objects.filter(equipe__in=equipes),
    villes = Ville.objects.filter(equipier__equipe__in=equipes).order_by('nom').annotate(equipiers=Count('equipier')),
    return render_to_response('stats.html', RequestContext(request, {
        'equipes': Equipe.objects.filter(course__uid=course_uid),
        'equipers': equipiers,
        'villes': villes,
    }))

