from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.views.generic import ListView
from models import Equipe

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
) + patterns('inscriptions.views',
    (r'(?P<course_uid>[^/]*)/vars.js$', TemplateView.as_view(template_name='vars.js')),
    (r'(?P<course_uid>[^/]*)/(?P<id>\d+)/done/$', 'done', {}, 'inscriptions.done'),
    (r'(?P<course_uid>[^/]*)/(?P<id>\d+)/(?P<code>\w+)/$', 'form', {}, 'inscriptions.edit'),
    (r'(?P<course_uid>[^/]*)/$', 'form', {}, 'inscriptions.create'),
    (r'(?P<course_uid>[^/]*)/ipn/$', 'ipn', {}, 'inscriptions.ipn'),
    (r'(?P<course_uid>[^/]*)/check_name/$', 'check_name', {}, 'inscriptions.check_name'),
    (r'(?P<course_uid>[^/]*)/list/$', 'list', {}, 'inscriptions.list'),
) + patterns('inscriptions.admin_views',
    (r'(?P<course_uid>[^/]*)/(?P<id>\d+)/send/(?P<template>.*)$', 'send_mail', {}, 'inscriptions.send_mail'),
    (r'(?P<course_uid>[^/]*)/dossards/$', 'dossards', {}, 'inscriptions.dossards'),
    (r'(?P<course_uid>[^/]*)/equipiers/$', 'equipiers', {}, 'inscriptions.equipiers'),
    (r'(?P<course_uid>[^/]*)/dossards.csv$', 'dossardsCSV', {}, 'inscriptions.dossardsCSV'),
    (r'(?P<course_uid>[^/]*)/dossards_equipes.csv$', 'dossardsEquipesCSV', {}, 'inscriptions.dossardsEquipesCSV'),
    (r'(?P<course_uid>[^/]*)/dossards_equipiers.csv$', 'dossardsEquipiersCSV', {}, 'inscriptions.dossardsEquipiersCSV'),
    (r'(?P<course_uid>[^/]*)/listing_dossards/$', 'listing_dossards', {}, 'inscriptions.listing_dossards'),
    (r'(?P<course_uid>[^/]*)/listing/$', 'listing', {}, 'inscriptions.listing'),
)
