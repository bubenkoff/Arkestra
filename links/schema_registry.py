from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from widgetry.utils import traverse_object
from widgetry.views import search, WrapperFactory, SearchItemWrapper, call_if_callable
from widgetry import signals as widgetry_signals


class LinkWrapper(SearchItemWrapper):
    # gets default identifier, title, description and thumbnail methods
    # from SearchItemWrapper

    def text(self):
        return call_if_callable(getattr(self.obj, 'text', self.title()))

    def short_text(self):
        return call_if_callable(getattr(self.obj, 'short_text', self.text()))

    def url(self):
        return call_if_callable(getattr(self.obj, 'get_absolute_url', ""))

    def metatag(self):
        return call_if_callable(getattr(self.obj, 'metatag', 'no metatag defined'))

    def heading(self):
        return call_if_callable(getattr(self.obj, 'heading', ''))


ATTRIBUTES = [
    # at least one of these is absolutely required
    'title',
    'text',

    # useful attributes
    'identifier',
    'description',
    'thumbnail_url',
    'short_text',
    'url',
    'metadata',
    'heading',  # the heading under which such items will be grouped
]


class MyWrapperFactory(WrapperFactory):
    pass


wrapper_factory = MyWrapperFactory(LinkWrapper, ATTRIBUTES)


class Registry(object):

    def __init__(self):
        self.wrappers = dict()
        self.content_types = dict()
        self.discovered = False
        # these signals make sure that whenever a widgetry function is used
        # the schemas from links are actually registered
        widgetry_signals.search_request.connect(self.discover_links_schemas)
        widgetry_signals.get_wrapper.connect(self.discover_links_schemas)

    def register(self, klasses, search_fields, **kwargs):
        # register with an autogenerated wrapper
        if not isinstance(klasses, list):
            klasses = [klasses]
        if not search_fields:
            raise Exception("link schema registration: search_fields are missing")
        for klass in klasses:
            wrapper = wrapper_factory.build(
                '%sAutoGenerated' % klass.__name__,
                search_fields, kwargs
                )
            self.register_wrapper(klass, wrapper)

    def register_wrapper(self, klasses, wrapper):
        # register with a manual wrapper
        if not isinstance(klasses, list):
            klasses = [klasses]
        for klass in klasses:
            #print u"registering %s to %s" % (klass, wrapper)
            self.wrappers[klass] = wrapper
            self.content_types[klass] = ContentType.objects.get_for_model(klass)
            # also register any links with the search/autocomplete system
            if not search.is_registered(klass):
                # but only if it is not registered yet
                #print u"schema: %s is already registerd for search, not adding" % klass
                search.register_wrapper(klass, wrapper)


    def get_wrapper(self, model_or_string):
        self.discover_links_schemas()
        #print "get wrapper %s" % model_or_string
        if isinstance(model_or_string, str):
            app_label, model_name = model_or_string.split('.')
            content_type = ContentType.objects.get(app_label=app_label, model=model_name)
            model = content_type.model_class()
        else:
            model = model_or_string
        #print "return wrapper for %s" % model
        #print self.wrappers
        if model in self.wrappers:
            wrapper = self.wrappers[model]
        else:
            wrapper = LinkWrapper
        #print "    wrapper: %s" % wrapper
        return wrapper

    def is_registered(self, model):
        self.discover_links_schemas()
        return model in self.wrappers

    def content_type_choices(self):
        self.discover_links_schemas()
        choices = [('','----')]
        #q_obj = None
        for model_class, content_type in self.content_types.items():
            #new_q = Q(app_label = model_class._meta.app_name, )
            choices.append((content_type.pk, u"%s: %s" % (content_type.app_label.replace('_', ' '), content_type.name)))
        return choices

    def discover_links_schemas(self, *args, **kwargs):
        '''
        run through all installed apps to find link schema definitions.
        This needs to get called rather late, because it needs access to
        models and admin
        '''
        if self.discovered:
            return
        for app in settings.INSTALLED_APPS:
            __import__(app, {}, {}, ['link_schemas'])
        self.discovered = True

schema = Registry()
