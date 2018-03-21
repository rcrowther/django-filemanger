The backend for the filemanager is abstracted and can be anything.



== The API

Start a db, stating the filesystem location of the database, ::

    from filemanager.db import DB

    db = DB('/home/rob/djangosites/uploads')

everything stems from this.

The only requirement on a db is that it can do this, ::

    db.collections.list()

and that existing clooections are available as attributes, ::

    db.images

Each collection must provide a simple CRUD interface, ::

    db.images.read(6)

...and a count, ::
 
    db.images.size()

The API makes one unusual demand, and that is each collection must make a manager called 'derived' available. 'derived' manages files derived from the main file upload. These may be compressed, run through effects, validated, etc. The derived API  must handle namespacing of derived subcollections. After that, it is simpler than the collection API, it asks only for read(), write() and clear(), and clear_type(), ::

    db.images.derived.read('32x32', 9)
    db.images.derived.clear_type('teaser')
    



== BucketDB
By default, and the only backend currently available, is 'bucketdb'. bucketdb stores files using the local filesystem (not, for example, in a database, or by some form of compression). Each table/collection gets a named folder, and within the folder are numbered buckets, set to contain a certain number of files. The number of files in a bucket is an internal preset, and irrelevant to the general API (management commands do exist to change the bucket size, though this is a complex and long-running process).

The reason for buckets is not, as used to be, because of the limits on folder content size, but so the database can be read and/or modified by simple tools (e.g. a GUI filebrowser would normally be capable of reading folders containing the default bucketsize of 256 files).

Within each bucket, files are inserted and named by the pk used. Note that this is not expected behaviour, intuitive behaviour would be to store by some identifier name for the content. If names are required it it expected these are maintained elsewhere, usually in a table contained in a database, alonside other information. The information stored in a database may, for example, be citation data, creation/upload dates etc. But though this is related to the file upload, it is not the upload itself.



== BucketDB extensions
BucketDB includes some extensions to the main API, ::

    DB.rescue(collection_name)

Will rebuild a header for the collection, if not present.

     DB.some_collection.manager

returns a collection to do various kinds of maintenence and analysis e.g.

    def rebuild_header(self, is_binary):
    def bucket_size_change(self, new_size):
    def clear(self):
    def size(self):
    def rebuild_size(self):
    def disk_storage_size(self):

NB: the size options report by physical scan, not by consulting cache.
