from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^zoo$', views.search, name='search'),
    #url(r'^(?P<paper_id>[0-9]+)/$', views.paper, name='paper'),
    #url(r'^file/(?P<file_id>[0-9]+)$', views.manage_files, name='file-form'),
    #url(r'^file/add$', views.file_add, name='file-add'),
]
