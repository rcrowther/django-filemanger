#from django.http import HttpResponseRedirect
#from django.shortcuts import render
from django import forms
from django.core.exceptions import ImproperlyConfigured

try:
    from quickviews import ModelCreateView, UpdateView, CreateView, ConfirmView
except ImportError:
    raise ImportError('The Filemanager.quickviews module requires the Quickviews app.')

from .db import DB



class UploadFileForm(forms.Form):
    file = forms.FileField()
    


class UploadFile(CreateView):
    form_class = UploadFileForm
    #! should include collection...
    db_path = None
    collection_name = None
    display_title = 'Upload {0}'
    success_message = "Uploaded {0}"
    
    def __init__(self, **kwargs):
        if ((not 'db_path' in kwargs) or (not kwargs['db_path'])):
            raise ImproperlyConfigured("{} must have a 'db_path' parameter".format(self.__class__.__name__))
        if ((not 'collection_name' in kwargs) or (not kwargs['collection_name'])):
            raise ImproperlyConfigured("{} must have a 'collection_name' parameter".format(self.__class__.__name__))
        super().__init__(**kwargs)

    def handle_uploaded_file(self, uploaded_file):
        db = DB(self.db_path)
        coll = db(self.collection_name)
        # use the callback to upload
        with coll.auto_create_cb() as path:
            with open(path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
                                
    def success_action(self, form):
        f = self.request.FILES['file']
        self.handle_uploaded_file(f)
        return str(f)
       



class UploadMultipleFileForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    

class UploadMultipleFiles(CreateView):
    form_class = UploadMultipleFileForm
    #! should include collection...
    db_path = None
    collection_name = None
    display_title = 'Upload {0}'
    success_message = "Uploaded {0}"

    def __init__(self, **kwargs):
        if ((not 'db_path' in kwargs) or (not kwargs['db_path'])):
            raise ImproperlyConfigured("{} must have a 'db_path' parameter".format(self.__class__.__name__))
        if ((not 'collection_name' in kwargs) or (not kwargs['collection_name'])):
            raise ImproperlyConfigured("{} must have a 'collection_name' parameter".format(self.__class__.__name__))
        super().__init__(**kwargs)

    def handle_uploaded_file(self, uploaded_file):
        db = DB(self.db_path)
        coll = db(self.collection_name)
        # use the callback to upload
        with coll.auto_create_cb() as path:
            with open(path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
    def success_action(self, form):
        files = self.request.FILES.getlist('file')
        b = []
        for f in files:
            self.handle_uploaded_file(f)
            b.append(str(f))
        return ', '.join(b)
       

#! wheres the pk for the one to change?
class UpdateFile(UpdateView):
    form_class = UploadFileForm
    #! should include collection...
    db_path = None
    collection_name = None
    url_pk_arg = 'pk'
    #display_title = 'Upload {0}'
    #success_message = "Uploaded {0}"

    def __init__(self, **kwargs):
        if ((not 'db_path' in kwargs) or (not kwargs['db_path'])):
            raise ImproperlyConfigured("{} must have a 'db_path' parameter".format(self.__class__.__name__))
        if ((not 'collection_name' in kwargs) or (not kwargs['collection_name'])):
            raise ImproperlyConfigured("{} must have a 'collection_name' parameter".format(self.__class__.__name__))
        super().__init__(**kwargs)

    def get_object(self):
        # override an initial load.
        return None

    def handle_uploaded_file(self, pk, uploaded_file):
        db = DB(self.db_path)
        coll = db(self.collection_name)
        # use the callback to upload
        with coll.update_cb(int(pk)) as path:
            with open(path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
                    
    def success_action(self, form):
        pk = self.kwargs.get(self.url_pk_arg)
        f = self.request.FILES['file']
        self.handle_uploaded_file(pk, f)
        return str(f)
        
        
        
#! need collection
#! needs redirecct
#! delete what, by name?
class DeleteView(ConfirmView):
    #! should include collection...
    db_path = None
    collection_name = None
    confirm_message = '<p>Are you sure you want to delete this file?</p>'
    success_message = "Deleted {0}"
    url_pk_arg = 'pk'
    success_url = '/filemanager'

    def __init__(self, **kwargs):
        if ((not 'db_path' in kwargs) or (not kwargs['db_path'])):
            raise ImproperlyConfigured("{} must have a 'db_path' parameter".format(self.__class__.__name__))
        if ((not 'collection_name' in kwargs) or (not kwargs['collection_name'])):
            raise ImproperlyConfigured("{} must have a 'collection_name' parameter".format(self.__class__.__name__))
        super().__init__(**kwargs)
    
    def get_object(self):
        # override an initial load.
        return None
        
    def success_action(self, form):
        pk = self.kwargs.get(self.url_pk_arg)
        db = DB(self.db_path)
        coll = db(self.collection_name)
        coll.delete(int(pk))
        return 'id:' + pk
