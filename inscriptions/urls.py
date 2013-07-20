from django.conf.urls.defaults import *
from django.views.generic import TemplateView
from django.views.generic import ListView
from models import Equipe

urlpatterns = patterns('inscriptions.views',
    (r'^vars.js$', TemplateView.as_view(template_name='vars.js')),
    (r'^(?P<id>\d+)/done/$', 'done', {}, 'inscriptions.done'),
    (r'^(?P<id>\d+)/send/(?P<template>.*)$', 'send_mail', {}, 'inscriptions.send_mail'),
    (r'^(?P<id>\d+)/(?P<code>\w+)/$', 'form', {}, 'inscriptions.edit'),
    (r'^$', 'form', {}, 'inscriptions.create'),
    (r'^ipn/$', 'ipn', {}, 'inscriptions.ipn'),
    (r'^check_name/$', 'check_name', {}, 'inscriptions.check_name'),
    (r'^list/$', 'list', {}, 'inscriptions.list'),
    (r'^bene/$', 'bene', {}, 'inscriptions.bene'),
    (r'^dossards/$', 'dossards', {}, 'inscriptions.dossards'),
    (r'^equipiers/$', 'equipiers', {}, 'inscriptions.equipiers'),
    (r'^dossards.csv$', 'dossardsCSV', {}, 'inscriptions.dossardsCSV'),
    (r'^dossards_equipes.csv$', 'dossardsEquipesCSV', {}, 'inscriptions.dossardsEquipesCSV'),
    (r'^dossards_equipiers.csv$', 'dossardsEquipiersCSV', {}, 'inscriptions.dossardsEquipiersCSV'),

)
