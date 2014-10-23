from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings

# enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # admin and admindocs
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # core Arkestra
    url(r'^semantic/', include('semanticeditor.urls')),
    url(r"", include("contacts_and_people.urls")),
    url(r"", include("links.urls")),

    # Javascript internationalisation
    url(
        r'^jsi18n/(?P<packages>\S+?)/$',
        'django.views.i18n.javascript_catalog'
        ),

    # widgetry autocomplete
    url('^autocomplete/$', 'widgetry.views.search', name='widgetry-search'),
)

if settings.DEBUG:
    urlpatterns+= static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += patterns('',
    url(r'^', include('cms.urls')),
)
