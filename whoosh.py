import os
from django.db.models import signals
from django.conf import settings
from whoosh import fields, index
#from whoosh.filedb import filestore
from .models import File
from whoosh.index import open_dir
from whoosh.index import create_in, exists_in


#class Field():
#    pass
from django.db import models
from django.apps import apps
from itertools import chain
from django.core.exceptions import (
    NON_FIELD_ERRORS, FieldError, ImproperlyConfigured
)
from whoosh.fields import FieldType
from .fields import *

#x Need the appname and modelname to make the index
# how does Models auto-initiate?
#x why not just build the schema init list?
# meta declaration is horrible?
# need the add/update triggers in there
# and first-time build
# options to be checked and go through
#x(better...) full set of fields
# and delete index what we have command.
# stemming
# absolute URL option

      
#! one needs to be 'unrecognised'?
def default_woosh_field(klass, **kwargs):
    '''
    Given a Model Field, return a guess for a Whoosh field.
    Intended as nest-guess at likely sense, not a definition of what can be done.
    '''
    #print('klass:' + str(klass))
    #print('klass ==:' + str(klass == models.DateField))

    if (klass == models.CharField):
        return TextField()
    if (
        klass == models.DateTimeField 
        or klass == models.DateField 
        or klass == models.EmailField
        or klass == models.URLField
        or klass == models.UUIDField
        ):
        return IdField
    return None


#class DefiningClass(type):
    #def __new__(mcs, name, bases, attrs):
        #new_class = super(DefiningClass, mcs).__new__(mcs, name, bases, attrs)
        #return new_class
        
        
#class DeclarativeFieldsMetaclass(DefiningClass):
class DeclarativeFieldsMetaclass(type):
    """Collect Fields declared on base classes."""
    def __new__(mcs, name, bases, attrs):
        # Collect fields from current class.
        #print('new DeclarativeFieldsMetaclass')
        current_fields = {}
        for k, v in list(attrs.items()):
            #print('key: '+str(k))
            if isinstance(v, FieldType):
                #print('v: '+str(v))
                current_fields[k] = v
                attrs.pop(k)
        #attrs['declared_fields'] = current_fields

        new_class = super(DeclarativeFieldsMetaclass, mcs).__new__(mcs, name, bases, attrs)

        # Walk through the MRO.
        base_fields = {}
        for base in new_class.__mro__:
            # Collect fields from base class.
            if hasattr(base, 'whoosh_fields'):
                base_fields.update(base.whoosh_fields)

            # Field shadowing.
            for attr, value in base.__dict__.items():
                if value is None and attr in base_fields:
                    base_fields.pop(attr)

        #new_class.base_fields = base_fields
        if (not hasattr(new_class, 'whoosh_fields')):
            new_class.whoosh_fields = {}
        new_class.whoosh_fields.update(base_fields)
        new_class.whoosh_fields.update(current_fields)

        #attrs['all_fields'] = chain(attrs['all_fields'], current_fields, declared_fields)
        #attrs['all_fields'].update(current_fields, declared_fields)
        #print('class fields: ' + str(attrs['all_fields']))

        return new_class
        
        

class WooshOptions:
    def __init__(self, app_label, module, class_name, options=None):
        self.whoosh_index = getattr(options, 'whoosh_index', None)
        if not self.whoosh_index:
            self.whoosh_index = "{0}_{1}".format(app_label, class_name)   
        self.module = module
        self.class_name = class_name
        self.fields = getattr(options, 'fields', None)
        self.schema_fields = []
        self.model = None

    def add_model_data(self, options=None):
        self.model = getattr(options, 'model', None)

    def __str__(self):
        return "WooshOptions(whoosh_index:{0}, module:{1}, model:{2}, fields:{3}, schema_fields:{4})".format(
        self.whoosh_index,
        self.module,
        self.model,
        self.fields,
        self.schema_fields
        )


class WooshMetaclass(DeclarativeFieldsMetaclass):
    def _schema_fields(mcs, field_data, opts):
        print('schema fields')
        fields = {}
        for f in opts.fields:
            if not (f in field_data):
                raise ImproperlyConfigured(
                    "Whoosh class {0}.{1} requested field {2} not declared.".format(opts.module, opts.class_name, f)
                )
            else:
              fields[f] = field_data[f]
        return fields
        
    def _first_run(mcs, whoosh_index, schema_fields):
        print('first run of derived type')
        #if not os.path.exists(settings.WHOOSH):
        #    os.mkdir(settings.WHOOSH)
            #storage = store.FileStorage(settings.WHOOSH_INDEX)
            #ix = index.Index(storage, schema=WHOOSH_SCHEMA, create=True)
        #create_in(dirname, schema, indexname=None):
        #exists_in(dirname, indexname=None):
        #destroy()
        if not exists_in(settings.WHOOSH, whoosh_index):
            whoosh_schema = fields.Schema(**schema_fields)
            create_in(settings.WHOOSH, whoosh_schema, whoosh_index)
        
    def __new__(mcs, name, bases, attrs):
        print('new WooshMetaclass : ' + name)
        
        opts = attrs.pop( 'Meta', None)

        # make the new class
        new_class = super(WooshMetaclass, mcs).__new__(mcs, name, bases, attrs)  


        module = attrs.pop('__module__')
        #print('meta meta:' + str(attrs))

        # get meta. Fail if none
        #! always is one now?
        #if not opts:
        #    raise ImproperlyConfigured(
        #        "Whoosh class {0}.{1} with no 'meta' attribute.".format(module, name)
        #    )

        print('meta meta:' + str(new_class.whoosh_fields))

        #new_class._meta = opts

        whoosh_index = getattr(opts, 'whoosh_index', None)
        app_label = getattr(opts, 'app_label', None)
        if ((whoosh_index is None) and (app_label is None)):
            app_config = apps.get_containing_app_config(module)
            if app_config is None:
                raise ImproperlyConfigured(
                    "Whoosh class {0}.{1} doesn't declare an explicit whoosh_index and isn't in an application in INSTALLED_APPS.".format(module, name)
                )
            else:
                app_label = app_config.label

        fields = getattr(opts, 'fields', None)
        if fields is None:
                raise ImproperlyConfigured(
                    "Whoosh class {0}.{1} doesn't declare a fields attribute.".format(module, name)
                )
       
        # We check if a string was passed to `fields`,
        # which is likely to be a mistake where the user typed ('foo') instead
        # of ('foo',)
        #value = getattr(opts, 'fields')
        if isinstance(fields, str):
            msg = "{0}s.Meta.fields cannot be a string. Did you mean to type: ('{1}s',)?".format(
                name,
                value,
                )
            raise TypeError(msg)

        new_class._meta = WooshOptions(app_label, module, name, opts) 
        schema_fields = new_class._meta.schema_fields = new_class._schema_fields(new_class.whoosh_fields, new_class._meta)
        new_class._first_run(new_class._meta.whoosh_index, schema_fields) 
        return new_class


class BaseWhoosh():
    #def __init__(self, whoosh_index=None):
        #opts = self._meta
        #if opts.model is None:
            #raise ValueError('ModelForm has no model class specified.')
        #pass
        #doc_count()
    #def open_dir(dirname, indexname=None, readonly=False, schema=None):


    def bulk_add(self, it):
        ix = open_dir(settings.WHOOSH, index_id)
        writer = ix.writer()
        for e in it:
            writer.add_document(e)
        writer.commit()      

    def add(self, **fields):
        '''
        Write a document.
        Ignores keys not in schema. None for unprovided schema keys.
        
        @param fields keys for the schema, values for values. 
        '''
        ix = open_dir(settings.WHOOSH, index_id)
        writer = ix.writer()
        writer.add_document(**fields)
        writer.commit()

    def clear(self):
        '''
        Empty the index.
        '''
        ix = open_dir(settings.WHOOSH, index_id)
        ix.destroy()

    def delete(self, fieldname, text):
        '''
        Delete a document.
        Match on any key.
        
        @param fieldname key to match against
        @param text match value. 
        '''
        ix = open_dir(settings.WHOOSH, index_id)
        writer = ix.writer()
        writer.delete_by_term(fieldname, text, searcher=None)
        writer.commit() 
        
    def merge(self, **fields):
        '''
        Merge a document.
        Ignores keys not in schema. None for unprovided schema keys.
        Checks for unique keys then matches against parameters.
        Much slower than add(), but will create.
        
        @param fields keys for the schema, values for values. 
        '''
        # "It is safe to use ``update_document`` in place of ``add_document``; if
        # there is no existing document to replace, it simply does an add."
        ix = open_dir(settings.WHOOSH, index_id)
        writer = ix.writer()
        writer.update_document(**fields)
        writer.commit() 

    def size(self):
        ix = open_dir(settings.WHOOSH, index_id)
        writer = ix.writer()
        r = writer.doc_count()
        writer.commit()
        return r
        
    def schema(self):
        return fields.Schema(**self.whoosh_fields)
            
    def optimize(self):
        ix = open_dir(settings.WHOOSH, index_id)
        ix.optimize()
        
        
class Whoosh(BaseWhoosh, metaclass=WooshMetaclass):
    class Meta:
        fields = []
        #pass
    #@classmethod


def fields_for_model(model, allowed_fields):
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
    not_recognised = {}
    #opts = model._meta
    # Avoid circular import
    #from django.db.models.fields import Field as ModelField
    #sortable_private_fields = [f for f in opts.private_fields if isinstance(f, ModelField)]
    for mf in model._meta.concrete_fields:
        name = mf.name 
        if name not in allowed_fields:
            continue

        kwargs = {}

        #if field_classes and f.name in field_classes:
        #    kwargs['form_class'] = field_classes[f.name]

        #formfield = f.formfield(**kwargs)
        wooshfield = default_woosh_field(mf)
        if wooshfield:
            field_list[name] = wooshfield
        else:
            not_recognised[name] = wooshfield.__class__.__name__

    return (field_list, not_recognised)

################################
#class ModelWooshMetaclass(DeclarativeFieldsMetaclass):
    #def _first_run(mcs, whoosh_index, whoosh_schema):
        #print('first run of derived type')
        #if not os.path.exists(settings.WHOOSH_INDEX):
            #os.mkdir(settings.WHOOSH_INDEX)
            ##storage = store.FileStorage(settings.WHOOSH_INDEX)
            ##ix = index.Index(storage, schema=WHOOSH_SCHEMA, create=True)
        ##create_in(dirname, schema, indexname=None):
        ##exists_in(dirname, indexname=None):
        ##destroy()
        ##create_in(settings.WHOOSH_INDEX, whoosh_schema, whoosh_index)
        
    #def __new__(mcs, name, bases, attrs):
        #print('new ModelWooshMetaclass : ' + name)
        
        #new_class = super(ModelWooshMetaclass, mcs).__new__(mcs, name, bases, attrs)

        ##if bases == (BaseWhoosh,):
        ##    return new_class
        ##print('meta class:' + str(new_class))
        ##print('meta dec fields:' + str(new_class.all_fields))
        
        
        
        #opts = new_class._meta = ModelWooshOptions(getattr(new_class, 'Meta', None))
        #print('meta meta:' + str(opts))


        ## We check if a string was passed to `fields`,
        ## which is likely to be a mistake where the user typed ('foo') instead
        ## of ('foo',)
        #value = getattr(opts, 'fields')
        #if isinstance(value, str):
            #msg = "{0}s.Meta.fields cannot be a string. Did you mean to type: ('{1}s',)?".format(
                #new_class.__name__,
                #value,
                #)
            #raise TypeError(msg)

        #if not opts.model:
            #raise ImproperlyConfigured(
                #"ModelWoosh with no 'model' attribute: model:{0}".format(
                #name
                #))

        #whoosh_index = getattr(opts, 'whoosh_index', None)
        #if whoosh_index is None:
            #module = attrs.pop('__module__')
            #app_config = apps.get_containing_app_config(module)
            #if app_config is None:
                #raise RuntimeError(
                    #"Model class %s.%s doesn't declare an explicit whoosh_index and isn't in an application in INSTALLED_APPS." % (module, name)
                #)
            #else:
                #whoosh_index = app_config.label + '_' + name
        #new_class.whoosh_index = whoosh_index 

                            
        #if opts.model != -1:
            ## this is a derived instance being instanciated.
            
            ## extract whoosh fields from the model.
            #if opts.fields is None:
                #raise ImproperlyConfigured(
                    #"ModelWoosh with no 'fields' attribute: model:{0}".format(
                    #name
                    #))
                
            #model_field_list = {field.name : field.__class__ for field in opts.model._meta.concrete_fields}
            #declared = new_class.all_fields
            
            ##print('model_field_list:' + str(model_field_list))
            ##print('model ignored:' + str(not_recognised))
            #unrecognised_field_names = []
            #not_defaulted_and_not_declared = {}
            #whoosh_fields = {}
            #for fieldname in opts.fields:
                ## is it in the model?
                #if (not(fieldname in model_field_list)):
                    #unrecognised_field_names.append(fieldname)
                    #continue
                ## is there an declared override?
                #r = declared.get(fieldname)
                #if (r):
                    #whoosh_fields[fieldname] = r 
                    #continue
                ## can it be defaulted?
                #r = default_woosh_field(model_field_list[fieldname])
                #if (r):
                    #whoosh_fields[fieldname] = r
                #else:
                    #not_defaulted_and_not_declared[fieldname] = model_field_list[fieldname].__name__

            #if (unrecognised_field_names):
                #raise ImproperlyConfigured(
                    #"'fields' attribute names field(s) not in stated Model: model:{0} fields:{1}".format(
                    #name,
                    #', '.join(unrecognised_field_names)
                    #))
                  
            #if (not_defaulted_and_not_declared):
                #raise ImproperlyConfigured(
                    #"ModelField(s) can not be defaulted. Try declaring the Whoosh field to use? : Model:{0} : fields:\n{1}".format(
                    #name,
                    #str(not_defaulted_and_not_declared)
                    #))
        ## Override default model fields with any custom declared ones
        ## (plus, include all the other declared fields).
        ##fields.update(new_class.all_fields)
        ##else:
        ##    fields = new_class.all_fields

        ##new_class.base_fields = fields
            ##new_class.whoosh_fields = fields
            #new_class._first_run(
            #whoosh_index,
            #fields.Schema(**whoosh_fields)
            #)

        #return new_class
########################

#class BaseWhoosh:
    #"""
    #The main implementation of all the Form logic. Note that this class is
    #different than Form. See the comments by the Form class for more info. Any
    #improvements to the form API should be made to this class, not to the Form
    #class.
    #"""
    ##default_renderer = None
    ##field_order = None
    ##prefix = None
    ##use_required_attribute = True
    #index_path=None
    
    #def __init__(self, index_path=None):
        #pass
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
        #self.fields = copy.deepcopy(self.base_fields)
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

#class ModelWhoosh(BaseModelWhoosh, metaclass=ModelWooshMetaclass):

    #class Meta:
        ## a sentinel
        #model = -1



#class FileSchema(ModelWhoosh):
  #class Meta:
    #woosh_index = 'modelwoosh'
    #app_label = 'modelwoosh'
    #model=File
    #fields = ['name', 'date', 'author']
    
#print('woosh prelim...')
WHOOSH_SCHEMA = fields.Schema(title=fields.TEXT(stored=True),
                              content=fields.TEXT,
                              url=fields.ID(stored=True, unique=True))
                              
#! in app, not in main site?
def create_index(sender=None, **kwargs):
    if not os.path.exists(settings.WHOOSH):
        os.mkdir(settings.WHOOSH)
        #storage = store.FileStorage(settings.WHOOSH)
        #ix = index.Index(storage, schema=WHOOSH_SCHEMA, create=True)
        create_in(settings.WHOOSH, WHOOSH_SCHEMA)


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
