from django.conf.urls import url
from . import quickviews

urlpatterns = [
    #url(r'^zoo$', views.search, name='search'),
    #url(r'^(?P<paper_id>[0-9]+)/$', views.paper, name='paper'),
    #url(r'^file/(?P<file_id>[0-9]+)$', views.manage_files, name='file-form'),
    #url(r'^file/add$', views.file_add, name='file-add'),
    ##
    url(r'^add$', quickviews.UploadFile.as_view(db_path='/home/rob/djangosites/uploads'), name='file-add'),
    #url(r'^add$', quickviews.UploadMultipleFiles.as_view(db_path='/home/rob/djangosites/uploads'), name='file-add'),
    url(r'^(?P<pk>[0-9]+)/update$', quickviews.UpdateFile.as_view(db_path='/home/rob/djangosites/uploads'), name='file-update'),
    url(r'^(?P<pk>[0-9]+)/delete$', quickviews.DeleteView.as_view(db_path='/home/rob/djangosites/uploads'), name='file-delete'),
]
