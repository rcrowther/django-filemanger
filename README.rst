Django filemanager
==================
A split app,

- A file storage facility with API
- Pre-built views

At present only one file storage IO ('backend') exists. It stores files as hard copy (regular filesystem files), in buckets (folders) of adjustable size. Due to the API, any other system can be built instead e.g. (the often badly-spoken of) storage to database, a single folder system, etc. 

Limitations
-----------
Untested in dev and production enviromnents (that's a crushing objection...)

No lock or transactions on the storage ('multithread' protection).

Views not filled out

Currently views are limited to simple form items (e.g. no Drag and Drop views) 
 
 
 
Alternatives
------------
Plenty,

https://djangopackages.org/packages/p/django-imagekit/

http://www.django-photologue.net/

https://djangopackages.org/packages/p/django-filebrowser/

The immense and must-be-mentioned,
    https://github.com/divio/django-filer/
    
    https://pypi.org/project/django-filer/
    
'Filer' covers most common scenarios which can arrise when handling files, it has file listings, form fields, thumbnailing, and more. So, some argument in the face of this, about why django-filemanager exists. It is because 'filer' is too immense for my usage. 'Filer' is also prescriptive about how to solve file management, yet there are many ways to solve the issues involved.



Installation/dependencies
--------------------------
Several of the views are 'Quickviews', though the app will install without dependency on Quickviews.
 
Place the app in a Django environment. Remove the 'django-' namespace from the top folder. 

In settings.py, add, ::

    INSTALLED_APPS = [
        ...
        'filemanager',
    ]


Configuring the 'bucket' IO
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The bucket IO configuration is free as the air we breathe. No kidding. It needs a path (like a Java DB), except this is a system filepath. The path is not configured overall. A Django-like approach to handling files as a project-wide action might be to add a setting in 'settings.py', ::

    UPLOAD_ROOT = os.path.join(BASE_DIR, 'uploads')

Or borrow some other suitable setting, ::

    MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')

Note that you should not use the STATIC_ROOT setting. Django separates this from MEDIA_ROOT so user-uploaded files are uploaded/served from a defined place which can have security measures applied.  

Usually, the root folder will be set so it can be served, ::

    STATICFILES_DIRS = [
        ...
        UPLOAD_ROOT
    ]

(presuming 'django.contrib.staticfiles') The above also makes the folder part of the 'collectstatic' mechanism,
see https://docs.djangoproject.com/en/2.0/howto/static-files/deployment/


Now use the setting in URL configuration and templating, ::

    from django.conf import settings
    
    # Can use this
    settings.UPLOAD_ROOT

For more on using BucketDB contents, see later. Also
https://docs.djangoproject.com/en/2.0/howto/static-files/.



Use of BucketDB
---------------

URL routing
~~~~~~~~~~~
URL e.g. ::

    url(r'^add$', quickviews.UploadMultipleFiles.as_view(db_path=settings.UPLOAD_ROOT, collection_name='images'), name='file-add'),


In 'debug' mode, look at files (currently fails as there are no extensions???) using a URL in this form, 'host/STATIC_URL/collection_name/bucket_num/file_id' e.g. ::

    http://127.0.0.1:8000/static/images/0/0

There are other ways of placing and handling the database (which is because of Django, not this app). The uploads can be placed in one app (e.g. the 'filemanager' app). The files can be deployed in various ways. Or may not be deployed, because production and dev uploads are not synchronised... 

In templates
~~~~~~~~~~~~
This is an example with very limited usage, to load entries in the 'bucket' database directly (it presumes png contents), ::

    {% load static %}
    
    <img src="{% static "images/0/17" %}" alt="Image alt text"/>

There are several problems here. The URL states the bucket, which is unecessary information. Better is the custom built-in template tag, ::

    {% load filemanager_tags %}
    
    <img src="{% bucketdb_static "images/17" %}" alt="Image alt text"/>

and another custom tag allows the colllection and pk to be passed as separate arguments, ::

    {% load filemanager_tags %}
    
    <img src="{% bucketdb_collection_static "images" 17 %}" alt="Image alt text"/>




