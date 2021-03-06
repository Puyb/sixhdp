from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.views.generic import ListView
from .models import Equipe
from .views import FactureView
#from admin_views import DossardsView

from inscriptions import admin

urlpatterns = patterns('',
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', { 'packages': ('inscriptions',), 'domain': 'djangojs' }),
    url(r'^admin/', include(admin.main_site.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    (r'^(?P<course_uid>[^/]+)/admin/$', admin.course_setter, {}, 'admin_course_setter'),
    url(r'^course/', include(admin.course_site.urls)),
) + patterns('inscriptions.views',
    (r'^$', 'index', {}, 'inscriptions.index'),
    (r'^(?P<course_uid>[^/]+)/vars.js$', TemplateView.as_view(template_name='vars.js')),
    (r'^(?P<course_uid>[^/]+)/(?P<numero>\d+)/done/$', 'done', {}, 'inscriptions.done'),
    (r'^(?P<course_uid>[^/]+)/(?P<numero>\d+)/facture/$', FactureView.as_view(), {}, 'inscriptions.facture'),
    (r'^(?P<course_uid>[^/]+)/(?P<numero>\d+)/(?P<code>\w+)/$', 'form', {}, 'inscriptions.edit'),
    (r'^(?P<course_uid>[^/]+)/$', 'form', {}, 'inscriptions.create'),
    (r'^(?P<course_uid>[^/]+)/imaginR/$', 'form', { 'imaginr': True }, 'inscriptions.createImaginR'),
    (r'^(?P<course_uid>[^/]+)/ipn/$', 'ipn', {}, 'inscriptions.ipn'),
    (r'^(?P<course_uid>[^/]+)/check_name/$', 'check_name', {}, 'inscriptions.check_name'),
    (r'^(?P<course_uid>[^/]+)/list/$', 'list', {}, 'inscriptions.list'),
    (r'^(?P<course_uid>[^/]+)/change/(?P<numero>\d+)/$', 'change', {}, 'inscriptions.change'),
    (r'^(?P<course_uid>[^/]+)/change/sent/$', 'change', { 'sent': True }, 'inscriptions.change_sent'),
    (r'^(?P<course_uid>[^/]+)/change/$', 'change', {}, 'inscriptions.change'),
    (r'^(?P<course_uid>[^/]+)/stats/$', 'stats', {}, 'inscriptions.stats'),
    (r'^(?P<course_uid>[^/]+)/stats/(?P<course_uid2>[^/]+)$', 'stats_compare', {}, 'inscriptions.stats_compare'),
) + patterns('inscriptions.admin_views',
    #(r'^(?P<course_uid>[^/]+)/dossards/$', DossardsView.as_view(), {}, 'inscriptions.dossards'),
    (r'^(?P<course_uid>[^/]+)/equipiers/$', 'equipiers', {}, 'inscriptions.equipiers'),
    (r'^(?P<course_uid>[^/]+)/dossards.csv$', 'dossardsCSV', {}, 'inscriptions.dossardsCSV'),
    (r'^(?P<course_uid>[^/]+)/dossards_equipes.csv$', 'dossardsEquipesCSV', {}, 'inscriptions.dossardsEquipesCSV'),
    (r'^(?P<course_uid>[^/]+)/dossards_equipiers.csv$', 'dossardsEquipiersCSV', {}, 'inscriptions.dossardsEquipiersCSV'),
    (r'^(?P<course_uid>[^/]+)/listing_dossards/$', 'listing_dossards', {}, 'inscriptions.listing_dossards'),
    (r'^(?P<course_uid>[^/]+)/listing/$', 'listing', {}, 'inscriptions.listing'),
)

