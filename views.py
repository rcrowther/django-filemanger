from django.shortcuts import render

from django.forms import ModelForm
from .models import File

from django import forms
from django.urls import reverse
from django.contrib import messages
import os
from django.conf import settings


## Overall
# different folders for different roles?
# same name differentiation?
# where to hold derived files?

## DBIO
# buckets
# admin fix
# folder writers
# Model
# enable types

## Models
#x get full data from Apertium wiki?
# add cite?

## forms
# auto-fill name from filename

## effects

## admin
# control types?

## upload
# quota?
# filesize
# munging
# mimes
# should apply the extension?
# multi-upload?

class FileForm(ModelForm):
    
    class Meta:
        model = File
        fields = ['name', 'path', 'author']
        #widgets={'path': forms.FileInput(attrs={'multiple': True})}
        #clean()
        
        
        
def store_uploaded_file(dst, f):
    with open(dst, 'wb+') as dst:
        for chunk in f.chunks():
            dst.write(chunk)
            
def file_add(request):
    if request.method == 'POST':
        f = FileForm(request.POST, request.FILES)
        if f.is_valid():
            #f.save()
            #print(str(f.cleaned_data))
            #print(f.cleaned_data['path'].name)
            #print(str(request.FILES))
            final_path = os.path.join(settings.MEDIA_ROOT, f.name)
            store_uploaded_file(final_path, f.cleaned_data['path'])
            
            #fm = File.system.save(
                #name=f.cleaned_data['name'], 
                #path=final_path, 
                #author=f.cleaned_data['author']
                #) 
            #msg = tmpl_instance_message("Added File", fm.name)
            msg = "Added File"
            messages.add_message(request, messages.SUCCESS, msg)       
    else:
        f = FileForm()
    context={
    'form': f,
    'title': 'Add File',
    #'navigators': [
    #  link('Term List', reverse('term-list', args=[bm.pk])),
    #  ],
    'submit': {'message':"Save", 'url': reverse('file-add')},
    #'submit': {'message':"Save"},
    'actions': [],
    } 
    return render(request, 'filemanager/generic_form.html', context)

def manage_files(request, file_id):
    fm = File.objects.get(pk=file_id)
    if request.method == 'POST':
        f = FileForm(request.POST, request.FILES)
        if f.is_valid():
            #fm = File.system.update(
                #name=f.cleaned_data['name'], 
                #author=f.cleaned_data['author']
                #) 
            #msg = tmpl_instance_message("Updated File", fm.name)
            msg = "Updated File"
            messages.add_message(request, messages.SUCCESS, msg)
            print(str(f.clean_data))
    else:
        f = FileForm()
        
    context={
    'form': f,
    'title': 'Add Term',
    #'navigators': [
    #  link('Term List', reverse('term-list', args=[bm.pk])),
    #  ],
    'submit': {'message':"Save", 'url': reverse('file-form', args=[file_id])},
    #'submit': {'message':"Save"},
    'actions': [],
    } 
    return render(request, 'filemanager/generic_form.html', context)
