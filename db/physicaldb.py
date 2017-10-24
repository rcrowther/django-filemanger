import os
from django.conf import settings
import shutil
import math


from .header import Header, DEFAULT_BUCKET_SIZE

class Derived:
    def __init__(self, db):
        self.db = db
        
    def _derived_path_from_pk(self, typ, pk):
        return os.path.join(self.db._path, self.db._bucket_from_pk(pk), 'derived', typ)
                
    def path(self, typ, pk):
        return os.path.join(self.db._path, self.db._bucket_from_pk(pk), 'derived', typ, str(pk))
                      
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


    def load(self, name):
        path = os.path.join(self.db.path, name)
        header_path = os.path.join(path, '.header')
        header = Header(header_path)
        header.load() 
        coll = Collection(name, path, header_path, header)
        setattr(self.db, name, coll)
    
    def delete(self, name):
        path = os.path.join(self.db.path, name)
        shutil.rmtree(path)
                 
    def list(self):
        return self.db.dirnames
           
           
            
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
    If a database is corrupt, it may not load Collections. Use the 
    rescue method(), ::
        rebuild_collection = DB.rescue('fireworks') 
    and go to work with the .manager. See manager in Collection.
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
        data = {}
        for bpath in bpaths:
            data[bpath] = list(self.coll._idpaths(bpath))
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

    #def defragment(self):
    
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
        Rest the header to a count of physical files.
        (may not be the same as the auto-pk count due to deletions)
        '''
        self.coll.header.size = self.size()
                                 
    #! could do by directory stat?
    def disk_storage_size(self):
        '''
        size in bytes of records.
        '''
        return sum(os.path.getsize(path) for path in self._paths_all())
                                   


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
        for bucket_id in os.listdir(self.path):
          p = os.path.join(self.path, bucket_id)
          if (os.path.isdir(p)):
            yield p 

    def _bucket_id_from_pk(self, pk):
        return str(math.floor(pk / self.header.bucket_size))

    def _bucket_path_from_pk(self, pk):
        return os.path.join(self.path, self._bucket_id_from_pk(pk))

    def _idpaths(self, bucketpath):
        for file_id in os.listdir(bucketpath):
          p = os.path.join(bucketpath, file_id)
          if (os.path.isfile(p)):
            yield p 
            

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
    Has a CRUD interface for updating.
    Collections are designated binary or text on creation.
    Administration is via. ::
        collection.manager
    that gives access to rebuild_header(), bucket_size_change(), 
    and disk_storage_size() etc. methods.
    Header info on the collection is available at, :: 
        <collection>.header
    that can be altered by assignment.
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


    def document_path(self, idx):
        return os.path.join(self.path, self._bucket_from_pk(idx), str(idx))
                    
    #-
    #def create(data):
        #self.header.next_pk()
        #self.update(self.header.last_pk, data)
        #self.header.size_inc()

    def create_cb(self, pk, data_create_callback):
        self.header.next_pk()
        self.update_cb(self.header.last_pk, data_create_callback)
        self.header.size_inc()

    def read(self, pk):
        assert isinstance(pk, int), "Not an integer"
        with open(self.document_path(pk), self.read_format) as f:
            o = f.read()
        return o
        
    def update(self, pk, data):
        assert isinstance(pk, int), "Not an integer"
        bp = self._bucket_path_from_pk(pk)
        os.makedirs(bp, exist_ok=True)
        path = os.path.join(bp, str(pk))
        with open(path, self.write_format) as f:
            f.write(data)

    def update_cb(self, pk, data_create_callback):
        '''
        Write an element.
        The method will not create the data, but ensures data can be
        created at the path passed to the callback.
        
        @param pk id to write at
        @param data_create_callback receives the path allocated for the data.
        '''
        assert isinstance(pk, int), "Not an integer"
        bp = self._bucket_path_from_pk(pk)
        os.makedirs(bp, exist_ok=True)
        path = os.path.join(bp, str(pk))
        data_create_callback(path)

    def delete(self, pk):
        assert isinstance(pk, int), "Not an integer"
        os.remove(self.document_path(pk))   
        self.header.size_dec()
    
    def size(self):
        return self.header.size


