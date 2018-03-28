


class Connection():
    def __init__(self, driver, db_name):
        pass
        
          
          
            
class DB():  
    self.collections = None

    def __init__(self, path):
        pass       
        
    def __call__(self, name):
        '''
        Return a collection from the database.
        A shortcut for db.collections.collection(name).
        '''
        return self.collections.collection(name)



        
class Collections:
    def __init__(self, db):
        self.db = db

    #def create(self, name, bucket_size=DEFAULT_BUCKET_SIZE, is_binary=False):
    #    pass
        
    def delete(self, name):
        '''
        Delete a collection.
        Destroys all data in a collection. 
        '''
        pass
        
    def __call__(self, name):
        '''
        A collection by name.
        As this method uses a name parameter, it can be used by code
        to access a collection. 
        '''
        pass

    def list(self):
        '''
        List all collections in this database.
        @return a list of collection names as strings. 
        '''
        pass
        
                           
class Collection():
    '''
    Represents a collection in the DB.
    Has a CRUD interface for updating. The methods auto_create() and
    auto_create_cb() will auto-generate ids. If you wish to supply uour 
    own pks, use create() and create_cb().
    Update commands (simply) overwrite existing files, creating if 
    necessary. If used for creation, they will not maintain header
    data correctly (assuming collection size() is unchanged, etc.)
    Collections are designated binary or text on creation.
    Administration is via. ::
        collection.manager
    that gives access to methods like rebuild_header(), 
    bucket_size_change(), and disk_storage_size().
    Header info on the collection is available at, :: 
        <collection>.header
    The header can be altered by assignment.
    Collections contain a second manager, ::
        <collection>.derived
    for subcollections of derived files.
    '''
    def __init__(self, name):
        self.name = name
        #self.derived = Derived(self)
         
    def create(pk, data):
        '''
        Create a new document, using supplied pk.
        '''
        pass     

    def create_cb(self, pk, src, data_create_callback):
        '''
        Create a new document, using supplied pk.
        This method will not create the data, but ensures data can be
        created at the path passed to the callback. For consistency,
        the callback should overwrite existing contents, and create
        if necessary ('w+' and 'wb+').
        
        @param pk id to write at
        @param data_create_callback signature <callback name>(src, dst).
        '''
        pass
                
    def auto_create(data):
        '''
        Create a new document, using auto-id generation.
        '''
        pass
        
    def auto_create_cb(self, src, data_create_callback):
        '''
        Create a new document, using auto-id generation.
        This method will not create the data, but ensures data can be
        created at the path passed to the callback. For consistency,
        the callback should overwrite existing contents, and create
        if necessary ('w+' and 'wb+').
        
        @param data_create_callback signature <callback name>(src, dst).
        '''
        pass
        
    def read(self, pk):
        '''
        Read an element.

        @param pk id to read from
        '''
        assert isinstance(pk, int), "Not an integer"
        pass
        
    def update(self, pk, data):
        '''
        Write an element.
        Overwrites existing content, creates if necessary.

        @param pk id to write at
        '''
        assert isinstance(pk, int), "Not an integer"
        pass

    def update_cb(self, pk, src, data_create_callback):
        '''
        Write an element.
        This method will not create the data, but ensures data can be
        created at the path passed to the callback. For consistency,
        the callback should overwrite existing contents, and create
        if necessary ('w+' and 'wb+').
        
        @param pk id to write at
        @param data_create_callback signature <callback name>(src, dst).
        '''
        assert isinstance(pk, int), "Not an integer"
        pass
        
    def delete(self, pk):
        assert isinstance(pk, int), "Not an integer"
        pass
    
    def size(self):
        pass



class Derived:
    '''
    Derived collections are a place to store modifications of files.
    Modifications of files are commonly used/required on websites. 
    Examples would be a short extract from a soundfile, or a thumbnail 
    of an image.
    The approach of this manager is not to modify material 
    supplied. The manager stashes the original data, and 
    provides methods to handle the production and storage of derived
    files. This is more expensive than modifying on input, but respects
    user information and allows the manager to be used for
    archiving.
    On disc, this implementation stores derived folders in subfolders of
    the bucket folders.
    The API treats derived files casually (unlike the original
    files). Derived files can be generated or deleted at any time and 
    deleted in bulk. An important feature is that all derived files must
    be given a 'type'. The type is a string of your choosing (derived 
    'types' are not checked or vaildated). A derived type might be, 
    for example, 'teaser' for a textfile, 'snippet' for soundfiles, or 
    '32x32' for image thumbnails. The 'type' makes bulk creation and 
    deletion fast and non-disruptive.
    '''
    def __init__(self, coll):
        self.coll = coll
              
    def write_cb(self, typ, pk, data_create_callback):
        '''
        Write a derived element.
        The method will not create the data, but ensures data can be
        created at the path passed to the callback.
        
        @param type str to identify type of the kind
        @param data_create_callback receives the path allocated for the data.
        '''
        pass

    def read(self, typ, pk):
        pass
                
    def delete(self, typ, pk):
        '''
        Quiet delete of a derived element. 
        '''
        pass         

    def clear_type(self, typ):
        '''
        Quiet delete of all derived elements of a type. 
        '''
        pass
         
    def clear(self):
        '''
        Quiet delete of all derived elements in a database. 
        '''
        pass
          
