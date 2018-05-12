from django.shortcuts import render
from django import forms
from django.urls import reverse
from django.contrib import messages
from django.conf import settings

import os

from django.forms import ModelForm
from .models import File
#from django.views import CreateView
#from django.views.generic.edit import CreateView


#class DDCreate(CreateView):
    #model = Paper
    #fields = ['title', 'slug', 'summary', 'body', 'author']
    
####
## Overall
# different folders for different roles?
# same name differentiation?
# where to hold derived files?
# databases are just configurable --- in GUI/DB messes stuff up
# ...same story for pipelines


## DBIO
#x buckets
#x admin fix
#x folder writers

## Models
#x get full data from Apertium wiki?
# add cite?

## forms
# auto-fill name from filename

## effects
#x image

## admin
# control types?
# list?
# search widget?
# autocomplete widget?

## upload
# quota?
# filesize
# munging
# mimes
# should apply the extension?
# multi-upload?

#from django.conf import settings
#from django.views.generic.simple import direct_to_template
#from whoosh import index, fields
#from whoosh.filedb import filestore
#from whoosh.qparser import QueryParser
#from .whoosh import WHOOSH
#from whoosh.index import open_dir
#from . import whoosh

# visuals
# stemming
# title search
# image results
# better zero results
#def search(request):
    #"""
    #Simple search view, which accepts search queries via url, like google.
    #Use something like ?q=this+is+the+serch+term
    #"""
    ##storage = filestore.FileStorage(settings.WHOOSH)
    ##ix = index.Index(storage, schema=WHOOSH_SCHEMA)
    #ix = open_dir(settings.WHOOSH)
    #hits = []
    #query = request.GET.get('q', None)
    #if query is not None and query != u"":
        ##print('whoosh query')
        ## Whoosh don't understands '+' or '-' but we can replace
        ## them with 'AND' and 'NOT'.
        #query = query.replace('+', ' AND ').replace(' -', ' NOT ')
        #parser = QueryParser("content", schema=ix.schema)
        #try:
            #qry = parser.parse(query)
            ##qry = parser.parse('document')
        #except:
            ## don't show the user weird errors only because we don't
            ## understand the query.
            ## parser.parse("") would return None
            #qry = None
            #hits = [{'title' :"nothing doing", 'url' :'nonsense/'}]

        #if qry is not None:
            #with ix.searcher() as searcher:
                #print('whoosh qry: ' + str(qry))
            ##searcher = ix.searcher()
            ##hits = [{'title' :"nothing/something", 'url' :'nonsense/'}]
                #hits = searcher.search(qry)
                ##print('whoosh hits: ' + str(hits))
                #context  = {
                #'query' : query,
                #'hits' : hits
                #}
                #return render(request, 'filemanager/search.html', context)     
        #else:
            #hits = [{'title' :"nothing finding", 'url' :'nonsense/'}]

          
    ##return direct_to_template(request, 'search.html',
    ##                          {'query': query, 'hits': hits})
    #context  = {
    #'query' : query,
    #'hits' : hits
    #}
    #return render(request, 'filemanager/search.html', context)
                              
#####
#def store_uploaded_file(dst, f):
    #with open(dst, 'wb+') as dst:
        #for chunk in f.chunks():
            #dst.write(chunk)

from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from django.http import HttpResponse

from django import forms

class FileForm(forms.Form):
    files = forms.FileField()


class Upload(FormView):
    def handle_uploaded_file(f):
        #with open('some/file/name.txt', 'wb+') as destination:
        #    for chunk in f.chunks():
        #        destination.write(chunk)
        print('handle files' +f)
            
    def form_valid(self, form):
        # save the file
        print('saving???'+ str(self.request.FILES['files']))
        handle_uploaded_file(self.request.FILES['files'])
        # redirect to get_success_url()
        return super().form_valid(form)
        
# Only used for the AJAX return
# The form is created directly in the template
class DDFileForm(forms.Form):
    files = forms.FileField()


#? Chunk upload
#? https://github.com/garmoncheg/django_multiuploader/blob/master/django_multiuploader/multiuploader/static/multiuploader/scripts/jquery.fileupload.js
# assignment_tag
# Multiple submits should pile up on a GET.
# POST is only used for true submission
class DDUpload(TemplateView):
    template_name = "filemanager/drag_and_drop_form.html"
    
    def get(self, request, *args, **kwargs):
        #print('GET kwargs:' + str(kwargs))
        #ctx = {}
        #return render(request, "filemanager/drag_and_drop_form.html", ctx)  
        return super().get(self, request, *args, **kwargs)   

    def post(self, request, *args, **kwargs):
         
         print('POST args:' + str(args))
         print('POST kwargs:' + str(kwargs))
         print('Post POST:' + str(request.POST))
         print('Post FILES:' + str(request.FILES))
         print('Post Query:' + str(request.POST.__dict__))
         # This may be AJAX (modern browsers with JS + D&D)
         # or stock (fallback option)
         # The JS adds a value so we know 
         if (request.POST.get('ajax')):
             print('= modern browser AJAX upload')
         else:
             print('= non-JS stock upload')
           
         response = HttpResponse('POST response')
         return response
        
    #def get():
    #    pass
        
    #if request.method == 'POST':
        #f = FileForm(request.POST, request.FILES)
        #if f.is_valid():
            ##f.save()
            ##print(str(f.cleaned_data))
            ##print(f.cleaned_data['path'].name)
            ##print(str(request.FILES))
            #final_path = os.path.join(settings.MEDIA_ROOT, f.name)
            #store_uploaded_file(final_path, f.cleaned_data['path'])
            
            ##fm = File.system.save(
                ##name=f.cleaned_data['name'], 
                ##path=final_path, 
                ##author=f.cleaned_data['author']
                ##) 
            ##msg = tmpl_instance_message("Added File", fm.name)
            #msg = "Added File"
            #messages.add_message(request, messages.SUCCESS, msg)       
    #else:
        #f = FileForm()
    #context={
    #'form': f,
    #'title': 'Add File',
    ##'navigators': [
    ##  link('Term List', reverse('term-list', args=[bm.pk])),
    ##  ],
    #'submit': {'message':"Save", 'url': reverse('file-add')},
    ##'submit': {'message':"Save"},
    #'actions': [],
    #} 
    #return render(request, 'filemanager/drag_and_drop_form.html', context)
    
#class FileForm(ModelForm):
    #class Meta:
        #model = File
        #fields = ['name', 'path', 'author']
        ##widgets={'path': forms.FileInput(attrs={'multiple': True})}
        ##clean()
        
        
        
#def store_uploaded_file(dst, f):
    #with open(dst, 'wb+') as dst:
        #for chunk in f.chunks():
            #dst.write(chunk)
            
#def file_add(request):
    #if request.method == 'POST':
        #f = FileForm(request.POST, request.FILES)
        #if f.is_valid():
            ##f.save()
            ##print(str(f.cleaned_data))
            ##print(f.cleaned_data['path'].name)
            ##print(str(request.FILES))
            #final_path = os.path.join(settings.MEDIA_ROOT, f.name)
            #store_uploaded_file(final_path, f.cleaned_data['path'])
            
            ##fm = File.system.save(
                ##name=f.cleaned_data['name'], 
                ##path=final_path, 
                ##author=f.cleaned_data['author']
                ##) 
            ##msg = tmpl_instance_message("Added File", fm.name)
            #msg = "Added File"
            #messages.add_message(request, messages.SUCCESS, msg)       
    #else:
        #f = FileForm()
    #context={
    #'form': f,
    #'title': 'Add File',
    ##'navigators': [
    ##  link('Term List', reverse('term-list', args=[bm.pk])),
    ##  ],
    #'submit': {'message':"Save", 'url': reverse('file-add')},
    ##'submit': {'message':"Save"},
    #'actions': [],
    #} 
    #return render(request, 'filemanager/generic_form.html', context)

#def manage_files(request, file_id):
    #fm = File.objects.get(pk=file_id)
    #if request.method == 'POST':
        #f = FileForm(request.POST, request.FILES)
        #if f.is_valid():
            ##fm = File.system.update(
                ##name=f.cleaned_data['name'], 
                ##author=f.cleaned_data['author']
                ##) 
            ##msg = tmpl_instance_message("Updated File", fm.name)
            #msg = "Updated File"
            #messages.add_message(request, messages.SUCCESS, msg)
            #print(str(f.clean_data))
    #else:
        #f = FileForm()
        
    #context={
    #'form': f,
    #'title': 'Add Term',
    ##'navigators': [
    ##  link('Term List', reverse('term-list', args=[bm.pk])),
    ##  ],
    #'submit': {'message':"Save", 'url': reverse('file-form', args=[file_id])},
    ##'submit': {'message':"Save"},
    #'actions': [],
    #} 
    #return render(request, 'filemanager/generic_form.html', context)
