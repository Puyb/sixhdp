from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('inscriptions.urls')),
)
urlpatterns += staticfiles_urlpatterns()
if settings.DEBUG:
    urlpatterns += patterns('',
        url(
            r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:],
            'django.views.static.serve',
            { 'document_root': settings.MEDIA_ROOT, }
        ),
    )

