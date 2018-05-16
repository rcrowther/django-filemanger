import os
import shutil
import math
import collections
from .header import Header, DEFAULT_BUCKET_SIZE



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
    def __init__(self, db):
        self.db = db
        
    def _derived_path_from_pk(self, typ, pk):
        #?
        return os.path.join(self.db._bucket_path_from_pk(pk), 'derived', typ)
                
    def path(self, typ, pk):
        #?
        return os.path.join(self.db._bucket_path_from_pk(pk), 'derived', typ, str(pk))
                      
    def write_cb(self, typ, pk, data_create_callback):
        '''
        Write a derived element.
        The method will not create the data, but ensures data can be
        created at the path passed to the callback.
        
        @param type str to identify type of the kind
        @param data_create_callback receives the path allocated for the data.
        '''
        dp = self._derived_path_from_pk(typ, pk)
        os.makedirs(dp, exist_ok=True)
        path = os.path.join(dp, str(pk))
        data_create_callback(path) 

    def read(self, typ, pk):
        with open(self.path(typ, pk), 'r') as f:
            o = f.read()
        return o
                
    def delete(self, typ, pk):
        '''
        Quiet delete of a derived element. 
        '''
        p = self.path(typ, pk)
        if (os.path.exists(p)):
            os.remove(p)         

    def clear_type(self, typ):
        '''
        Quiet delete of all derived elements of a type. 
        '''
        for bucketpath in self.db._bucketpaths():
            p = os.path.join(bucketpath, 'derived', typ)
            if (os.path.exists(p)):
                shutil.rmtree(p)
         
    def clear(self):
        '''
        Quiet delete of all derived elements in a database. 
        '''
        for bucketpath in self.db._bucketpaths():
            p = os.path.join(bucketpath, 'derived')
            if (os.path.exists(p)):
                shutil.rmtree(p)
        
    def __repr__(self):
        return '<Derived path="{}">'.format(
            self.db.path
        )
        
        
class Collections:
    def __init__(self, db):
        self.db = db
        
    def create(self, name, bucket_size=DEFAULT_BUCKET_SIZE, is_binary=False):
        path = os.path.join(db.path, name)
        if os.path.exists(path):
            raise Exception('collection "{}" requested but exists'.format(
                name
            ))
        os.makedirs(path, exist_ok=True)
        header_path = os.path.join(path, '.header')
        header = Header(header_path)
        header.create(
            header_path, 
            bucket_size=bucket_size, 
            is_binary=is_binary
        )        
        coll = Collection(name, path, header_path, header)       
        setattr(self.db, name, coll)        

    def __call__(self, name):
        '''
        Return a collection of the given name.
        If it fails a header, FileNotFoundError
        '''
        path = os.path.join(self.db.path, name)
        header_path = os.path.join(path, '.header')
        header = Header(header_path)
        header.load() 
        return Collection(name, path, header_path, header)
        
    def load(self, name):
        '''
        Set a collection on the collections attributes.
        Used by DB to simplify the syntax of commandline and fixed-code 
        access.
        '''
        coll = self(name)
        setattr(self.db, name, coll)
    
    def delete(self, name):
        path = os.path.join(self.db.path, name)
        shutil.rmtree(path)
                 
    def list(self):
        return self.db.dirnames
           
           
#? make a fixed property?
class DB():       
    '''
    Access the physical DB.
    Collections are managed through, ::
        DB.collections
    Collections must be created() and deleted() (and list()ed)
    expicitly, ::
        DB.collections.create('fireworks')
    Collections are text by default, but can be binary. Collections have also a
    bucket_size, default 125, ::
        DB.collections.create('fireworks', bucket_size=512, is_binary=True)
    Collections can be accessed by name e.g. ::
        DB.fireworks
    if you intend to do much manipulation in one shot, stash, ::
        coll = DB.fireworks
    If a database is corrupt, it may not load auto-load damaged 
    Collections. Use the rescue method() to return a (dummy, it has no 
    content modification methods) RebuildCollection, ::
        rebuild_collection = DB.rescue('fireworks') 
    and go to work with the .manager e.g. ::
        rebuild_collection.manage.rebuild_header(is_binary=True)
    See manager in Collection.
    ''' 
    def __init__(self, path):
        self.path = path
        filepaths = [os.path.join(path, f) for f in os.listdir(path)]
        self.dirpaths = [p for p in filepaths if os.path.isdir(p)]
        self.dirnames = [os.path.basename(p) for p in self.dirpaths]
        self.collections = Collections(self)
        try:
            for name in self.dirnames:
                #coll = Collection(name)
                #coll.contribute_to_class(self.path)
                #setattr(self, cname, coll)       
                self.collections.load(name)
        except Exception:
            print('failed to load collections to DB at path {}'.format(path))
            #raise Exception('Problem encountered trying to open DB at {0}. Perhaps database is damaged somewhere?')
          
    def rescue(self, collection_name):
        '''
        Fix failed dbs.
        @return a collection which asserts headers and offers
        structural modification and repair.
        '''
        path = os.path.join(self.path, collection_name)
        if (not os.path.exists(path)):
            raise FileNotFoundError('not found file for rescue path: {0}'.format(
                path
                ))
        header_path = os.path.join(path, '.header')
        return RebuildCollection(collection_name, path, header_path)

    def __call__(self, name):
        '''
        Return a collection from the database.
        A shortcut for db.collections.collection(name).
        '''
        return self.collections(name)

    def __repr__(self):
        return '<DB path="{}">'.format(
            self.path
        )



class Manager():
    def __init__(self, coll):
        self.coll = coll
        
    def _max_bucketsize(self):
        max_size = 0
        for bucketpath in self.coll._bucketpaths():
            max_size = max(max_size, len(os.listdir(bucketpath)))
        return max_size

    def _document_path_to_id_str(self, document_path):
        str_id = os.path.basename(document_path)
        # remove extensions
        return str_id.split('.', 1)[0]
        
    def _max_id(self, bucketpath):
        '''
        -1 if fail
        '''
        max_id = -1
        id_paths = self.coll._idpaths(bucketpath)
         
        for id_path in id_paths:
            x = None
            try:
                x = int(self._document_path_to_id_str(id_path))
            except:
                pass
            if (x):
                max_id = max(max_id, x)
        return max_id
        
    def _pk_last(self):
        '''
        Find the last pk.
        Surveys the exisiting db. The method starts at the last folder, 
        looks for files, backs through folders until an element-like 
        file is found. Not guaranteed, but may help for rescue work.
        @return integer, -1 if fail
        '''
        maxpk = -1
        maxbucketpk = -1
        bp_map = {os.path.basename(bp) : bp for bp in self.coll._bucketpaths()}
        bkeys_as_int = []
        for bucket_id in bp_map.keys():
            x = None
            try:
                x = int(bucket_id)
            except:
                pass
            if (not(x is None)):
                bkeys_as_int.append(x)
        bkeys_as_int.sort()
        while (bkeys_as_int):
            topkey = bkeys_as_int.pop()
            bucketpath = bp_map[str(topkey)]            
            maxpk = self._max_id(bucketpath)
            if (maxpk != -1):
                break
        return maxpk

    def _paths_all(self):
        '''
        Walk all records in the db.
        Slow, this method looks for physical files. It also 
        tests files are file (not directories). It does not test for 
        symlinks, which will be followed.
        '''
        for bucketpath in self.coll._bucketpaths():
            for path in self.coll._idpaths(bucketpath):
                    yield path

                    
    def rebuild_header(self, is_binary):
        '''
        Create a header by surveying an existing db.
        For maintenence. Will look through the db and count
        bucketsizes etc. The method assumes the db contents are text,
        not binary.
        If the resulting values are known to be incorrect, that can be
        easily queried and modified using 
        db.<collection>.header properties. 
        return True is the db was surveyed and a header set, else False
        '''
        # assert a header
        if (not os.path.exists(self.coll.header_path)):
            self.coll.header = Header(self.coll.header_path).create()
        # rebuild from physical info
        pk_last = self._pk_last()
        if (pk_last != -1): 
            self.coll.header._set_all(
                last_id=pk_last, 
                bucket_size=self._max_bucketsize(), 
                size=self.size(),
                is_binary=is_binary
                )
            return True
        else:
            return False

                         
    def bucket_size_change(self, new_size):
        '''
        Change the size of bucket.
        Consider: this method will delete derived material, and may be
        expensive to use.
        The method is a generator which must be iterated.
        @yield tuple of elements moved () iteration
        returns
        '''
        self.coll.derived.clear()
        # can change the size - _bucketpaths() does not use it.
        self.coll.header.bucket_size = new_size
        # generated paths should be resolved to lists. Otherwise, we risk
        # horrors like recursive file generation, walking new file sets...
        bpaths = list(self.coll._bucketpaths())
        #data = {}
        #for bpath in bpaths:
        #    data[bpath] = list(self.coll._idpaths(bpath))
        data = { bpath : list(self.coll._idpaths(bpath)) for bpath in bpaths}
        for bucketpath, old_paths in data.items():
            for old_path in old_paths:
                pk = self._document_path_to_id_str(old_path)  
                new_bucket_path = self.coll._bucket_path_from_pk(int(pk))
                new_path = os.path.join(new_bucket_path, pk)
                if (new_path != old_path):
                    # make sure directory is there...
                    os.makedirs(new_bucket_path, exist_ok=True)
                    os.rename(old_path, new_path) 
                    yield (old_path, new_path) 
                
    def ids_compact(self):
        '''
        Compact the bucket contents and id sequence.
        Consider: this method will delete derived material, and may be
        expensive to use.
        The method will create missing buckets.
        The method is a generator which must be iterated.
        @yield tuples of ids moved (from, to)
        '''
        self.coll.derived.clear()
        # generated paths should be resolved to lists. Otherwise, we risk
        # horrors like recursive file generation, walking new file sets...
        bpaths = list(self.coll._bucketpaths_sorted())
        current_id = 0
        for bpath in bpaths:
            epaths = self.coll._idpaths_sorted(bpath)
            for edata in epaths:
                new_path = self.coll.asserted_document_path(current_id)
                # move with a little protection
                #? 'rename' fails  on Windows if an errant file exists
                #? should catch this? logger?
                if (edata.path != new_path):
                    os.rename(edata.path, new_path)
                    #print('move' + edata.path + ': ' + new_path)
                    yield (edata.id, current_id)
                current_id += 1
        self.coll.header.last_id=current_id - 1
        # can be here positivly asserted        
        self.coll.header.size=current_id       
                        
    def clear(self):
        shutil.rmtree(self.coll.path)

    def size(self):
        '''
        Number of files in the base.
        (may not be the same as the auto-pk count due to deletions)
        Physical count. Could be mislead if the filebase contains stray 
        files.
        '''
        return sum(1 for _ in self._paths_all())
      
    def rebuild_size(self):
        '''
        Reset the header to a count of physical files.
        (may not be the same as the auto-pk count due to deletions)
        '''
        self.coll.header.size = self.size()
                                 
    #! could do by directory stat?
    def disk_storage_size(self):
        '''
        size in bytes of records.
        '''
        return sum(os.path.getsize(path) for path in self._paths_all())
                                   



EntryData = collections.namedtuple('EntryData', 'id path')

class CollectionBase():

    def __init__(self, name, path, header_path):
        self.name = name
        self.path = path
        self.header_path = header_path
        self.derived = Derived(self)
        self.manager = Manager(self)
        
    def _bucket_path(self, bucket_id):
        return os.path.join(self.path, str(bucket_id))

    def _bucketpaths(self):
        '''
        Generator of paths to buckets.
        Filters for directories. Arbitary order. 
        '''
        for bucket_id in os.listdir(self.path):
          p = os.path.join(self.path, bucket_id)
          if (os.path.isdir(p)):
            yield p 

    def _bucketpaths_sorted(self):
        '''
        Generator of paths to buckets.
        Filters for directories with names coercable to int(). Ordered. 
        '''
        bucket_names = os.listdir(self.path)
        bucket_ids = []
        for name in bucket_names:
            try:
                bucket_ids.append(int(name))
            except ValueError:
                pass
        bucket_ids.sort()

        for bid in bucket_ids:
            p = os.path.join(self.path, str(bid))
            if (os.path.isdir(p)):
                yield p 
            
    def _bucket_id_from_pk(self, pk):
        return str(math.floor(pk / self.header.bucket_size))

    def _bucket_path_from_pk(self, pk):
        return os.path.join(self.path, self._bucket_id_from_pk(pk))
        
    def _idpaths(self, bucketpath):
        '''
        Generator of paths to files in a bucketpath.
        Filters for files. Arbitary order. 
        '''
        for file_id in os.listdir(bucketpath):
          p = os.path.join(bucketpath, file_id)
          if (os.path.isfile(p)):
            yield p 

    
    def _idpaths_sorted(self, bucketpath):
        '''
        Generator of paths to files in a bucketpath.
        Filters for entry files with names coercable to int(). Ordered. 
        '''
        entry_names = os.listdir(bucketpath)
        entry_ids = []
        for name in entry_names:
            try:
                entry_ids.append(int(name))
            except ValueError:
                pass
        entry_ids.sort()

        for eid in entry_ids:
            p = os.path.join(bucketpath, str(eid))
            if (os.path.isfile(p)):
                yield EntryData(eid, p)             


class RebuildCollection(CollectionBase):
    def __init__(self, name, path, header_path):
        super().__init__(name, path, header_path)

        # supply a dummy header. This will be filled with default,
        # but management methods write to it, for 
        # rebuilding, not consult it.
        self.header = Header(header_path)

        #  if not present, create the header
        if (not os.path.exists(header_path)):
            self.header.create()
            
                            
class Collection(CollectionBase):
    '''
    Represents a collection in the DB.
    Has a CRUD interface for updating. The methods auto_create() and
    auto_create_cb() will auto-generate ids. Ids are numbered from 0. If
    you wish to supply pks, use create() and create_cb().
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
    def __init__(self, name, path, header_path, header):
        super().__init__(name, path, header_path)

        self.header = header
        if (not header.is_binary):
            self.read_format = 'r'
            self.write_format = 'w'
        else:
            self.read_format = 'rb'
            self.write_format = 'wb'

    def path(self, pk):
        '''
        The full path to a document.
        This is a virtual construction. There is no guarentee the 
        document exists, only that if it did, it would be found here.
        '''
        return os.path.join(self._bucket_path_from_pk(pk), str(pk))
        
    def document_path(self, pk):
        '''
        The full path to a document.
        This is a virtual construction. There is no guarentee the 
        document exists, only that if it did, it would be found here.
        '''
        return os.path.join(self._bucket_path_from_pk(pk), str(pk))

    def document_relpath(self, pk):
        '''
        The path to a document, relative from and including the DB foldername.
        This is a virtual construction. There is no guarentee the 
        document exists, only that if it did, it would be found here.
        '''
        return os.path.join(self.name, self._bucket_id_from_pk(pk), str(pk))

    def relpath(self, pk):
        '''
        The path to a document, relative from and including the DB foldername.
        This is a virtual construction. There is no guarentee the 
        document exists, only that if it did, it would be found here.
        '''
        return os.path.join(self.name, self._bucket_id_from_pk(pk), str(pk))
        
    def relpaths(self, range):
        '''
        Yield paths to documents, relative from and including the DB foldername.
        These are virtual constructions. There is no guarentee the 
        documents exist, only that if they did, they would be found here.
        '''
        
        for pk in range:
            yield os.path.join(self.name, self._bucket_id_from_pk(pk), str(pk))
        
    def asserted_document_path(self, pk):
        '''
        Path with guaranteed existing bucket folder structure.
        Will make the folder structure if it does not exist.
        '''
        assert isinstance(pk, int), "Not an integer"
        bp = self._bucket_path_from_pk(pk)
        os.makedirs(bp, exist_ok=True)
        return os.path.join(bp, str(pk))

        assert isinstance(pk, int), "Not an integer"
        bp = self._bucket_path_from_pk(pk)
        os.makedirs(bp, exist_ok=True)
        path = os.path.join(bp, str(pk))
                
    def create(pk, data):
        '''
        Create a new document, using supplied pk.
        This method will destroy data with pks following the given pk.
        Data destruction will make sizes inaccurate.
        '''
        path = self.update(pk, data)
        self.header.last_id = pk
        self.header.size_inc()
        return path

    def create_cb(self, pk):
        '''
        Create a new document, using supplied pk.

        This method will not create the data, but ensures data can be
        created at the path passed to the 'with'. For consistency,
        the code should overwrite existing contents, and create
        if necessary ('w+' and 'wb+').
        
        Usage ::
            with db.some_collection.create_cb(pk) as path:
                some code
                
        @param pk id to write at
        '''
        class Create:
            def __init__(self, pk, header, asserted_path_from_pk):
                self.pk = pk
                self.header = header
                self.asserted_path_from_pk = asserted_path_from_pk

            def __enter__(self):
                path = self.asserted_path_from_pk(self.pk)
                return path
    
            def __exit__(self, type, value, traceback):
                self.header.last_id = self.pk
                self.header.size_inc()

        return Create(pk, self.header, self.asserted_document_path)
                                                      
    def auto_create(data):
        '''
        Create a new document, using auto-id generation.
        '''
        #? reverse these actions for write failure protection?
        self.header.next_id()
        path = self.update(self.header.last_id, data)
        self.header.size_inc()
        return path

    def auto_create_cb(self):
        '''
        Create a new document, using auto-id generation.

        This method will not create the data, but ensures data can be
        created at the path passed to the 'with'. For consistency,
        the code should overwrite existing contents, and create
        if necessary ('w+' and 'wb+').
        
        Usage ::
            with db.some_collection.auto_create_cb as path:
                some code
        '''
        class AutoCreate:
            def __init__(self, header, asserted_path_from_pk):
                self.header = header
                self.asserted_path_from_pk = asserted_path_from_pk

            def __enter__(self):
                self.header.next_id()
                pk = self.header.last_id
                path = self.asserted_path_from_pk(pk)
                return path
    
            def __exit__(self, type, value, traceback):
                self.header.size_inc()

        return AutoCreate(self.header, self.asserted_document_path)
        
    def read(self, pk):
        assert isinstance(pk, int), "Not an integer"
        with open(self.document_path(pk), self.read_format) as f:
            o = f.read()
        return o
        
    def update(self, pk, data):
        '''
        Write an element.
        Overwrites existing content, creates if necessary.

        @param pk id to write at
        '''
        #assert isinstance(pk, int), "Not an integer"
        #bp = self._bucket_path_from_pk(pk)
        #os.makedirs(bp, exist_ok=True)
        #path = os.path.join(bp, str(pk))
        path = self.asserted_document_path(pk)
        with open(path, self.write_format) as f:
            f.write(data)
        return path
            
    def update_cb(self, pk):
        '''
        Overwrites existing content, creates if necessary.

        This method will not create the data, but ensures data can be
        created at the path passed to the 'with'. For consistency,
        the code should overwrite existing contents, and create
        if necessary ('w+' and 'wb+').
        
        Usage ::
            with db.some_collection.create_cb(pk) as path:
                some write code
                
        @param pk id to write at
        '''
        class Update:
            def __init__(self, pk, header, asserted_path_from_pk):
                self.pk = pk
                self.header = header
                self.asserted_path_from_pk = asserted_path_from_pk

            def __enter__(self):
                path = self.asserted_path_from_pk(self.pk)
                return path
    
            def __exit__(self, type, value, traceback):
                pass

        return Update(pk, self.header, self.asserted_document_path)
                    
        
    def delete(self, pk):
        assert isinstance(pk, int), "Not an integer"
        #! delete derived also
        os.remove(self.document_path(pk))   
        self.header.size_dec()
    
    def size(self):
        return self.header.size

    def __str__(self):
        return '<Collection "{}">'.format(
            self.name
        )
        
    def __repr__(self):
        return "<Collection name={}, path={}>".format(
            self.name,
            self.path
        )

