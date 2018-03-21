import os

from django.contrib import admin
from django.conf.urls import url

#from .. import views
from django.shortcuts import render

from django.forms import ModelForm

from django import forms
from django.urls import reverse
from django.contrib import messages
from django.conf import settings

from quickviews import views
from ..models import File
from ..db.physicaldb import DB


#! not adding the index stuff.

db = DB(os.path.join(settings.BASE_DIR, 'uploads'))
coll = db.images

class FileForm(ModelForm):
    class Meta:
        model = File
        fields = ['name', 'description', 'author']
        #widgets={'path': forms.FileInput(attrs={'multiple': True})}
        #clean()
        
        

def uploaded_file_move_to_db(src, dst):
    with open(dst, 'wb+') as f:
        for chunk in src.chunks():
            f.write(chunk)
                        
class FileCreate(views.ModelCreate):
    model = File
    form_class = FileForm
    object_title_field = 'name'


    def create(self, cleaned_data):
        print('create_object')
        print(str(cleaned_data))
        #! dont know size until physical save
        #! don't know pk until text save
        obj = File.system.create(
            name=cleaned_data['name'], 
            description=cleaned_data['description'],
            path='uploads/images/0/', 
            author=cleaned_data['author'],
            #size=cleaned_data['size'],
            size=2000,
            #licence=cleaned_data['licence']
            licence='fleece'
        ) 
        # use the file pk, not an auto-generated one.
        #pk = cleaned_data['pk']
        #coll.create_cb(pk, cleaned_data['path'], uploaded_file_move_to_db)
        return obj
        

class FileUpdate(views.ModelUpdate):
    model = File
    form_class = FileForm
    object_title_field = 'name'

    def get_objects(self, url_args):
        print('get_objects')
        print(str(url_args))
        return File.objects.get(pk = url_args['file_id'])
        
    def update(self, pk, cleaned_data):
        print('update_object')
        print(str(cleaned_data))
        print(str(pk))
        obj = File.system.update(
              pk=pk,
              name=cleaned_data['name'], 
              description=cleaned_data['description'],
              path='uploads/images/0/', 
              author=cleaned_data['author'],
              #size=cleaned_data['size'],
              size=2000,
              #licence=cleaned_data['licence']
              licence='fleece'
        )
        return obj



class FileDelete(views.ModelDeleteConfirm):
    model = File
    object_title_field = 'name' 
    #success_redirect = reverse('filemanager-search')
    #success_redirect = '/admin/filemanager/file/search'
    message_directions = '<p>Deleting a file will not remove associated physical files.</p>'
    success_redirect_as_admin_base = True
    
    def get_objects(self, url_args):
        print('get_objects')
        print(str(url_args))
        return File.objects.get(pk = url_args['file_id'])

    def get_context_data(self, request, ctx):
        ctx = super().get_context_data(request, ctx)
        return_link = views.link('No, take me back', ctx['view'].get_admin_base_url(), attrs={'class':'"button"'})
        ctx['actions'].append(return_link)
        return ctx 

    def modify(self, obj):
        print('delete_object')
        print(str(obj))
        obj.delete()



from need import SearchHitView
from ..need import FileNeed

class FileSearchHitView(SearchHitView):
    need = FileNeed
    search_fields = 'name'

    def indexdata_to_renderdata(self, result):
        return {'url' : "/admin/filemanager/file/{}".format(result['id']), 'title': result['name'], 'teaser': result['description']}
  

class FileAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super(FileAdmin, self).get_urls()
        new_urls = [
          url(r'^$', FileSearchHitView.as_view(), name='filemanager-search'),
          url(r'^(?P<file_id>[0-9]+)/delete/$', FileDelete.as_view(), name='filemanager-delete'),
          url(r'^(?P<file_id>[0-9]+)/edit/$', FileUpdate.as_view(), name='filemanager-update'),
          url(r'^add/$', FileCreate.as_view(), name='filemanager-add'),
          url(r'^search/$', FileSearchHitView.as_view(), name='filemanager-search'),
        ]
        #print (str(new_urls + urls))
        return new_urls + urls   #+ super(FileAdmin, self).get_urls()
