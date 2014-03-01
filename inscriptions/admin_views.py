# -*- coding: utf-8 -*-
from models import Equipe, Equipier, TemplateMail
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError, Http404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.core.mail import EmailMessage
from django.utils.http import urlencode
from django.db.models import Count
import urllib2
import random
from settings import *
from threading import Thread
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import csv, cStringIO

@login_required
def send_mail(request, course_uid, id, template):
    course = get_object_or_404(Course, uid=course_uid)
    instance = get_object_or_404(Equipe, id=id, course=course)

    if request.method == 'POST':
        msg = EmailMessage(request.POST['subject'], request.POST['message'], request.POST['sender'], [ request.POST['mail'] ])
        msg.content_subtype = "html"
        msg.send()
        messages.add_message(request, messages.INFO, u'Message envoyé à %s' % (request.POST['mail'], ))
        return redirect('/admin/inscriptions/equipe/%s/' % (instance.id, ))


    mail = get_object_or_404(TemplateMail, id=template, course__uid=course_uid)
    sujet = render_to_string(mail.sujet, { "instance": instance, })
    message = render_to_string(mail.message, { "instance": instance, })

    return render_to_response('send_mail.html', RequestContext(request, {
        'message': message,
        'sender': course.email_contact,
        'mail': instance.gerant_email,
        'subject': sujet,
    }))

@login_required
def dossards(request, course_uid):
    return render_to_response('dossards.html', RequestContext(request, {
        'equipiers': Equipier.objects.filter(course__uid=course_uid).order_by(*request.GET.get('order','equipe__numero,numero').split(','))
    }))

@login_required
def listing(request, course_uid, template='listing.html'):
    return render_to_response(template, RequestContext(request, {
        'equipes': Equipe.objects.filter(course__uid=course_uid).order_by(*request.GET.get('order','id').split(','))
    }))

@login_required
def listing_dossards(request, course_uid, template='listing_dossards.html'):
    equipes = Equipe.objects.exclude(categorie__startswith='ID').order_by(*request.GET.get('order','id').split(','))
    return render_to_response(template, RequestContext(request, {
        'solo': Equipe.objects.filter(course__uid=course_uid, categorie__startswith='ID').order_by(*request.GET.get('order','id').split(',')),
        'equipes': {
            u'1 à 100':   equipes.filter(id__lt=101),
            u'101 à 145': equipes.filter(id__gt=100, id__lt=146),
            u'146 à 190': equipes.filter(id__gt=145, id__lt=191),
            u'191 à 239': equipes.filter(id__gt=190),
        }
    }))

def equipiers(request, course_uid):
    return render_to_response('equipiers.html', RequestContext(request, {
        'equipiers': Equipier.objects.filter(equipe__course__uid=course_uid)
    }))

#@login_required
def dossardsCSV(request, course_uid):
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
    for e in Equipier.objects.filter(equipe__course__uid=course_uid):
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

def dossardsEquipesCSV(request, course_uid):
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
    for e in Equipe.objects.filter(course__uid=course_uid):
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

def dossardsEquipiersCSV(request, course_uid):
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
    for e in Equipier.objects.filter(equipe__course__uid=course_uid):
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


