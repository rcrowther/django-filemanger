import os
from django.db.models import signals
from django.conf import settings
from whoosh import fields, index
#from whoosh.filedb import filestore
from .models import File
from whoosh.index import open_dir
from whoosh.index import create_in


#class Field():
#    pass
from django.db import models
from django.apps import apps
from itertools import chain
from django.core.exceptions import (
    NON_FIELD_ERRORS, FieldError, ImproperlyConfigured
)
from whoosh.fields import FieldType

# Need the appname and modelname to make the index
# how does Models auto-initiate?
# why not just build the schema init list?
# meta declaration is horrible?
# need the add/update triggers in there
# and first-time build
# options to be checked and go through
#x(better...) full set of fields
# and delete what we have command.
# stemming
# absolute URL option

class IntegerField(fields.NUMERIC):
    def __init__(self, stored=False, unique=False,
                 field_boost=1.0, decimal_places=0, shift_step=4, signed=True,
                 sortable=False, default=None)
        super().__init__(int, 32, stored, unique,
                 field_boost, decimal_places, shift_step, signed,
                 sortable, default)
                 
class LongField(fields.NUMERIC):
    def __init__(self, stored=False, unique=False,
                 field_boost=1.0, decimal_places=0, shift_step=4, signed=True,
                 sortable=False, default=None)
        super().__init__(long, 64, stored, unique,
                 field_boost, decimal_places, shift_step, signed,
                 sortable, default)
                                  
class FloatField(fields.NUMERIC):
    def __init__(self, stored=False, unique=False,
                 field_boost=1.0, decimal_places=0, shift_step=4, signed=True,
                 sortable=False, default=None)
        super().__init__(float, 32, stored, unique,
                 field_boost, decimal_places, shift_step, signed,
                 sortable, default)         

class DateTimeField(fields.DATETIME):
    def __init__(self, stored=False, unique=False, sortable=False):
        super().__init__(stored, unique, sortable)

class BooleanField(fields.BOOLEAN):
    def __init__(self, stored=False, field_boost=1.0):
        super().__init__(self, stored, field_boost):

class StoredField(fields.STORED):
    def __init__(self):
        pass
       
class KeywordField(fields.KEYWORD):
    def __init__(self, stored=False, lowercase=False, commas=False,
                 scorable=False, unique=False, field_boost=1.0, sortable=False,
                 vector=None, analyzer=None):
        super().__init__(stored, lowercase, commas,
                 scorable, unique, field_boost, sortable,
                 vector, analyzer)
        
class IdField(fields.ID):
    def __init__(self, stored=False, unique=False, field_boost=1.0,
                 sortable=False, analyzer=None):
        super().__init__(stored, unique, field_boost,
                 sortable, analyzer)

                 
class TextField(fields.TEXT):
    def __init__(self, analyzer=None, phrase=True, chars=False, stored=False,
                 field_boost=1.0, multitoken_query="default", spelling=False,
                 sortable=False, lang=None, vector=None,
                 spelling_prefix="spell_"):
        super().__init__(analyzer, phrase, chars, stored,
                 field_boost, multitoken_query, spelling,
                 sortable, lang, vector,
                 spelling_prefix)

class NGamWordsField(fields.NGRAMWORDS):
    def __init__(self, minsize=2, maxsize=4, stored=False, field_boost=1.0,
                 tokenizer=None, at=None, queryor=False, sortable=False):
        super().__init__(minsize, maxsize, stored, field_boost,
                 tokenizer, at, queryor, sortable)


      
#! one needs to be 'unrecognised'?
def to_field(klass, **kwargs):
    '''
    Intended as sense, not a definition of what can be done.
    '''
    if (klass == models.CharField):
        return TextField()
    if (
        klass == models.DateTimeField 
        or klass == DateField 
        or klass == EmailField
        or klass == URLField
        or klass == UUIDField
        ):
        return IdField
    return None


class DefiningClass(type):
    def __new__(mcs, name, bases, attrs):
        new_class = super(DefiningClass, mcs).__new__(mcs, name, bases, attrs)
        return new_class
        
        
class DeclarativeFieldsMetaclass(DefiningClass):
    """Collect Fields declared on the base classes."""
    def __new__(mcs, name, bases, attrs):
        print('new DeclarativeFieldsMetaclass')
        # Collect fields from current class.
        print('new DeclarativeFieldsMetaclass')
        current_fields = []
        for key, value in list(attrs.items()):
            if isinstance(value, FieldType):
                current_fields.append((key, value))
                attrs.pop(key)
        attrs['declared_fields'] = current_fields

        new_class = super(DeclarativeFieldsMetaclass, mcs).__new__(mcs, name, bases, attrs)

        # Walk through the MRO.
        declared_fields = {}
        for base in new_class.__mro__:
            # Collect fields from base class.
            if hasattr(base, 'declared_fields'):
                declared_fields.update(base.declared_fields)

            # Field shadowing.
            for attr, value in base.__dict__.items():
                if value is None and attr in declared_fields:
                    declared_fields.pop(attr)

        new_class.base_fields = declared_fields
        new_class.declared_fields = declared_fields

        return new_class

    @classmethod
    def __prepare__(metacls, name, bases, **kwds):
        # Remember the order in which form fields are defined.
        return {}

class ModelWooshOptions:
    def __init__(self, app_label=None, options=None):
        self.app_label = app_label
        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.field_classes = getattr(options, 'field_classes', None)
        
class Options:
    def __init__(self, meta, app_label=None):
        self.app_label = app_label
        self.meta = meta
        self.local_fields = []

    def _prepare(self, model):
        # in original, finds pk etc.
        pass



def fields_for_model(model, *, fields=None, field_classes=None):
    """
    Return an ``OrderedDict`` containing form fields for the given model.

    ``fields`` is an optional list of field names. If provided, return only the
    named fields.

    ``exclude`` is an optional list of field names. If provided, exclude the
    named fields from the returned fields, even if they are listed in the
    ``fields`` argument.

    ``widgets`` is a dictionary of model field names mapped to a widget.

    ``formfield_callback`` is a callable that takes a model field and returns
    a form field.

    ``localized_fields`` is a list of names of fields which should be localized.

    ``labels`` is a dictionary of model field names mapped to a label.

    ``help_texts`` is a dictionary of model field names mapped to a help text.

    ``error_messages`` is a dictionary of model field names mapped to a
    dictionary of error messages.

    ``field_classes`` is a dictionary of model field names mapped to a form
    field class.

    ``apply_limit_choices_to`` is a boolean indicating if limit_choices_to
    should be applied to a field's queryset.
    """
    field_list = {}
    opts = model._meta
    # Avoid circular import
    #from django.db.models.fields import Field as ModelField
    #sortable_private_fields = [f for f in opts.private_fields if isinstance(f, ModelField)]
    for f in opts.concrete_fields:
        if f.name not in fields:
            continue

        kwargs = {}

        if field_classes and f.name in field_classes:
            kwargs['form_class'] = field_classes[f.name]

        #formfield = f.formfield(**kwargs)
        formfield = to_field(f.__class__)
        if formfield:
            field_list[f.name] = formfield
        else:
            ignored.append(f.name)

    return field_list


class ModelWooshMetaclass(DeclarativeFieldsMetaclass):
    def __new__(mcs, name, bases, attrs):
        print('new ModelWooshMetaclass')
        new_class = super(ModelWooshMetaclass, mcs).__new__(mcs, name, bases, attrs)

        if bases == (BaseWhoosh,):
            return new_class

        opts = new_class._meta = ModelWooshOptions('whoosh-app', getattr(new_class, 'Meta', None))

        # We check if a string was passed to `fields` or `exclude`,
        # which is likely to be a mistake where the user typed ('foo') instead
        # of ('foo',)

        value = getattr(opts, 'fields')
        if isinstance(value, str):
            msg = ("%(model)s.Meta.%(opt)s cannot be a string. "
                   "Did you mean to type: ('%(value)s',)?" % {
                       'model': new_class.__name__,
                       'opt': opt,
                       'value': value,
                   })
            raise TypeError(msg)

        if opts.model:
            # If a model is defined, extract whoosh fields from it.
            if opts.fields is None:
                raise ImproperlyConfigured(
                    "Creating a ModelWoosh without the 'fields' attribute "
                    "is prohibited; Woosh %s "
                    "needs updating." % name
                )

            fields = fields_for_model(
                opts.model, fields=opts.fields, field_classes=opts.field_classes
            )
            print( str(fields))
            # make sure opts.fields doesn't specify an invalid field
            none_model_fields = {k for k, v in fields.items() if not v}
            missing_fields = none_model_fields.difference(new_class.declared_fields)
            if missing_fields:
                message = 'Unknown field(s) (%s) specified for %s'
                message = message % (', '.join(missing_fields),
                                     opts.model.__name__)
                raise FieldError(message)
            # Override default model fields with any custom declared ones
            # (plus, include all the other declared fields).
            fields.update(new_class.declared_fields)
        else:
            fields = new_class.declared_fields

        new_class.base_fields = fields

        return new_class

class BaseWhoosh:
    """
    The main implementation of all the Form logic. Note that this class is
    different than Form. See the comments by the Form class for more info. Any
    improvements to the form API should be made to this class, not to the Form
    class.
    """
    #default_renderer = None
    #field_order = None
    #prefix = None
    #use_required_attribute = True
    index_path=None
    
    def __init__(self, index_path=None):
        #self.is_bound = data is not None or files is not None
        #self.data = {} if data is None else data
        #self.files = {} if files is None else files
        #self.auto_id = auto_id
        #if prefix is not None:
        #    self.prefix = prefix
        #self.initial = initial or {}
        #self.error_class = error_class
        # Translators: This is the default suffix added to form field labels
        #self.label_suffix = label_suffix if label_suffix is not None else _(':')
        #self.empty_permitted = empty_permitted
        #self._errors = None  # Stores the errors after clean() has been called.

        # The base_fields class attribute is the *class-wide* definition of
        # fields. Because a particular *instance* of the class might want to
        # alter self.fields, we create self.fields here by copying base_fields.
        # Instances should always modify self.fields; they should not modify
        # self.base_fields.
        self.fields = copy.deepcopy(self.base_fields)
        #self._bound_fields_cache = {}
        #self.order_fields(self.field_order if field_order is None else field_order)

        #if use_required_attribute is not None:
        #    self.use_required_attribute = use_required_attribute

        # Initialize form renderer. Use a global default if not specified
        # either as an argument or as self.default_renderer.
        #if renderer is None:
            #if self.default_renderer is None:
                #renderer = get_default_renderer()
            #else:
                #renderer = self.default_renderer
                #if isinstance(self.default_renderer, type):
                    #renderer = renderer()
        #self.renderer = renderer

       
#class Whoosh(BaseWhoosh, metaclass=DeclarativeFieldsMetaclass):
#    pass
    
class BaseModelWhoosh(BaseWhoosh):
    def __init__(self, whoosh_index=None):
        opts = self._meta
        if opts.model is None:
            raise ValueError('ModelForm has no model class specified.')

    def schema(self):
        return fields.Schema(**self.base_fields)
            
          
#class ModelBase(type):
    #"""Metaclass for all models."""
    #def add_to_class(cls, name, value):
       #setattr(cls, name, value)
       
       
    #def __new__(cls, name, bases, attrs):
      
        #super_new = super().__new__

        ## Also ensure initialization is only performed for subclasses of Model
        ## (excluding Model class itself).
        #parents = [b for b in bases if isinstance(b, ModelBase)]
        #if not parents:
            #return super_new(cls, name, bases, attrs)

        ## Create the class.
        #module = attrs.pop('__module__')
        #new_attrs = {'__module__': module}
        ##...
        #new_class = super_new(cls, name, bases, new_attrs)
        #app_label = None
        #meta = None
        #app_config = apps.get_containing_app_config(module)
        #if app_config is None:
            #raise RuntimeError(
                #"Model class %s.%s doesn't declare an explicit "
                #"app_label and isn't in an application in "
                #"INSTALLED_APPS." % (module, name)
            #)
        #else:
            #app_label = app_config.label
        #new_class.add_to_class('_meta', Options(meta, app_label))

        ## Add all attributes to the class.
        #for obj_name, obj in attrs.items():
            #new_class.add_to_class(obj_name, obj)
        ## All the fields of any type declared on this model
        #new_fields = chain(
            #new_class._meta.local_fields,
            ##new_class._meta.local_many_to_many,
            ##new_class._meta.private_fields
        #)
        #field_names = {f.name for f in new_fields}
        #new_class._prepare()
        ##! put back
        ##new_class._meta.apps.register_model(new_class._meta.app_label, new_class)
        #return new_class


    #def _prepare(cls):
        #"""Create some methods once self._meta has been populated."""
        #opts = cls._meta
        #opts._prepare(cls)

        ##if opts.order_with_respect_to:
            ##cls.get_next_in_order = curry(cls._get_next_or_previous_in_order, is_next=True)
            ##cls.get_previous_in_order = curry(cls._get_next_or_previous_in_order, is_next=False)

            ### Defer creating accessors on the foreign class until it has been
            ### created and registered. If remote_field is None, we're ordering
            ### with respect to a GenericForeignKey and don't know what the
            ### foreign class is - we'll add those accessors later in
            ### contribute_to_class().
            ##if opts.order_with_respect_to.remote_field:
                ##wrt = opts.order_with_respect_to
                ##remote = wrt.remote_field.model
                ##lazy_related_operation(make_foreign_order_accessors, cls, remote)

        ## Give the class a docstring -- its definition.
        #if cls.__doc__ is None:
            #cls.__doc__ = "%s(%s)" % (cls.__name__, ", ".join(f.name for f in opts.fields))

        ##get_absolute_url_override = settings.ABSOLUTE_URL_OVERRIDES.get(opts.label_lower)
        ##if get_absolute_url_override:
        ##    setattr(cls, 'get_absolute_url', get_absolute_url_override)

        ##if not opts.managers:
            ##if any(f.name == 'objects' for f in opts.fields):
                ##raise ValueError(
                    ##"Model %s must specify a custom Manager, because it has a "
                    ##"field named 'objects'." % cls.__name__
                ##)
            ##manager = Manager()
            ##manager.auto_created = True
            ##cls.add_to_class('objects', manager)

        #class_prepared.send(sender=cls)

#class ModelForm(BaseModelForm, metaclass=ModelFormMetaclass):
#    pass
#class Model(metaclass=ModelBase):
# a = ModelWhoosh(File)

class ModelWhoosh(BaseModelWhoosh, metaclass=ModelWooshMetaclass):
        pass


class FileSchema(ModelWhoosh):
  model = File
  
  name = TextField(
    stored=True
    #unique=True
    )
  date = IdField
  author = IdField
  
#print('woosh prelim...')
WHOOSH_SCHEMA = fields.Schema(title=fields.TEXT(stored=True),
                              content=fields.TEXT,
                              url=fields.ID(stored=True, unique=True))
                              
#! in app, not in main site?
def create_index(sender=None, **kwargs):
    if not os.path.exists(settings.WHOOSH_INDEX):
        os.mkdir(settings.WHOOSH_INDEX)
        #storage = store.FileStorage(settings.WHOOSH_INDEX)
        #ix = index.Index(storage, schema=WHOOSH_SCHEMA, create=True)
        create_in(settings.WHOOSH_INDEX, WHOOSH_SCHEMA)


# not exists
#signals.post_syncdb.connect(create_index)
#  django.db.models.signals.pre_migrate¶



def update_index(sender, instance, created, **kwargs):
    #storage = filestore.FileStorage(settings.WHOOSH_INDEX)
    #ix = index.Index(storage, schema=WHOOSH_SCHEMA)
    ix = open_dir(settings.WHOOSH_INDEX)
    writer = ix.writer()
    if created:
        writer.add_document(title=instance.title, content=instance.body,
                                    url=instance.get_absolute_url())
        writer.commit()
    else:
        writer.update_document(title=instance.title, content=instance.body,
                                    url=instance.get_absolute_url())
        writer.commit()

def index_add():
    ix = open_dir(settings.WHOOSH_INDEX)
    writer = ix.writer()
    writer.add_document(title='Saxon-English man loses at tombola', content='A Whitworth man who bought a ticket for a tombola failed to win a prize',
                                 url='filemanager/file/9')
    ##writer.add_document(title='Brexit Politics', content='Policies criticised after national scandal',
      #                            url='filemanager/file/2')
    writer.commit()
    print('added?')
signals.post_save.connect(update_index, sender=File)
