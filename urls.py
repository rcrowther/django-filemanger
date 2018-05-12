from django.conf.urls import url
from . import quickviews
from .views import DDUpload
from django.conf import settings

urlpatterns = [
    #url(r'^zoo$', views.search, name='search'),
    #url(r'^(?P<paper_id>[0-9]+)/$', views.paper, name='paper'),
    #url(r'^file/(?P<file_id>[0-9]+)$', views.manage_files, name='file-form'),
    #url(r'^file/add$', views.file_add, name='file-add'),
    ##
    #url(r'^add$', quickviews.UploadFile.as_view(db_path='/home/rob/djangosites/uploads', collection_name='images'), name='file-add'),
    url(r'^ddadd$', DDUpload.as_view()),
    #url(r'^add$', quickviews.UploadFile.as_view(db_path='/home/rob/djangosites/uploads', collection_name='images'), name='file-add'),
    url(r'^add$', quickviews.UploadMultipleFiles.as_view(db_path=settings.UPLOAD_ROOT, collection_name='images'), name='file-add'),
    url(r'^(?P<pk>[0-9]+)/edit$', quickviews.UpdateFile.as_view(db_path=settings.UPLOAD_ROOT, collection_name='images'), name='file-update'),
    url(r'^(?P<pk>[0-9]+)/delete$', quickviews.DeleteView.as_view(db_path=settings.UPLOAD_ROOT, collection_name='images'), name='file-delete'),
]
