# -*- coding: utf-8 -*-
from models import Equipe, Equipier, TemplateMail
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError, Http404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.utils.http import urlencode
from django.db.models import Count
import urllib2
import random
from settings import *
from threading import Thread
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
import csv, cStringIO

@login_required
def dossards(request, course_uid):
    return render_to_response('dossards.html', RequestContext(request, {
        'equipiers': Equipier.objects.filter(course__uid=course_uid).order_by(*request.GET.get('order','equipe__numero,numero').split(','))
    }))

@login_required
def listing(request, course_uid, template='listing.html'):
    return render_to_response(template, RequestContext(request, {
        'equipes': Equipe.objects.filter(course__uid=course_uid).order_by(*request.GET.get('order','numero').split(',')),
        'order': request.GET.get('order','numero')
    }))

@login_required
def listing_dossards(request, course_uid, template='listing_dossards.html'):
    equipes = Equipe.objects.filter(course__uid=course_uid).order_by(*request.GET.get('order','numero').split(','))
    splits = ('1,' + request.GET.get('split', '1000')).split(',')
    splits = map(int, splits)
    datas = {}
    keys = []
    for i in range(len(splits) - 1):
        key = u'%d à %d' % (splits[i], splits[i + 1] - 1)
        datas[key] = equipes.filter(numero__gte=splits[i],  numero__lt=splits[i + 1])
        keys.append(key)

    return render_to_response(template, RequestContext(request, { 'equipes': datas, 'keys': keys }))

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


