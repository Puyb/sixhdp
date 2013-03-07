from django.conf.urls.defaults import *
from django.views.generic import TemplateView
from models import Equipe

urlpatterns = patterns('inscriptions.views',
    (r'^vars.js$', TemplateView.as_view(template_name='vars.js')),
    (r'^(?P<id>\d+)/done/$', 'done', {}, 'inscriptions.done'),
    (r'^(?P<id>\d+)/(?P<code>\w+)/$', 'form', {}, 'inscriptions.edit'),
    (r'^$', 'form', {}, 'inscriptions.create'),
    (r'^ipn/$', 'ipn', {}, 'inscriptions.ipn'),

)
