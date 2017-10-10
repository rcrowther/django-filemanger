import os
from django.conf import settings
import shutil
import math


# from filemanager.physicaldb import *

class Derived:
    def __init__(self, db):
        self.db = db
        
    def _derived_path_from_pk(self, typ, pk):
        return os.path.join(self.db._path, self.db._bucket_from_pk(pk), 'derived', typ)
                
    def path(self, typ, pk):
        return os.path.join(self.db._path, self.db._bucket_from_pk(pk), 'derived', typ, str(pk))
                      
    def write(self, typ, pk, data_create_callback):
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
          
          
                 
class PhysicalDB():
    def __init__(self, path_stub, bucket_size=4):
        self._path = os.path.join(settings.BASE_DIR, path_stub)
        self.bucket_size = bucket_size
        self.derived = Derived(self)
        
    def _bucket_from_pk(self, pk):
        return str(math.floor(pk / self.bucket_size))

    def _bucket_path_from_pk(self, pk):
        return os.path.join(self._path, self._bucket_from_pk(pk))

    def _bucket_path(self, bucket_id):
        return os.path.join(self._path, str(bucket_id))


                    
    def bucket_size_change(self, new_size):
        '''
        Change the size of bucket.
        Consider: this method will delete derived material, and may be
        expensive to use.
        The method is a generator which must be iterated.
        @yield tuple of elements moved () iteration
        returns
        '''
        self.derived.clear()
        # can change the size - _bucketpaths() does not use it.
        self.bucket_size = new_size
        for bucketpath in self._bucketpaths():
            for pk in os.listdir(bucketpath):
                # must join this path, methods not valid
                old_path = os.path.join(bucketpath, pk)  
                new_bucket_path = self._bucket_path_from_pk(int(pk))
                new_path = os.path.join(new_bucket_path, str(pk))
                if (new_path != old_path):
                    # make sure directory is there...
                    os.makedirs(new_bucket_path, exist_ok=True)
                    os.rename(old_path, new_path) 
                    yield (old_path, new_path)
          
    #def defragment(self):

    def pk_last(self):
        '''
        @return integer, -1 if fail
        '''
        maxpk = -1
        maxbucketpk = -1
        for bucket_id in os.listdir(self._path):
            maxbucketpk = max(maxbucketpk, int(bucket_id))
        # if fails, back up...
        pklist = os.listdir(self._bucket_path(maxbucketpk))
        while (maxbucketpk > -1 and (not pklist)):
            maxbucketpk = maxbucketpk - 1
            bp = self._bucket_path(maxbucketpk)
            if(os.path.exists(bp)):
                pklist = os.listdir(self._bucket_path(maxbucketpk))
        if (maxbucketpk != -1):
            for pk in pklist:
                maxpk = max(maxpk, int(pk))  
        return maxpk

    def path(self, idx):
        return os.path.join(self._path, self._bucket_from_pk(idx), str(idx))
                    
    def _bucketpaths(self):
        for bucket_id in os.listdir(self._path):
            yield os.path.join(self._path, bucket_id)
            
    def paths_all(self):
        '''
        Walk all records in the db.
        Slow, this method looks for physical files. It also 
        tests files are file (not directories ). It does not test for 
        symlinks, which will be followed.
        '''
        for bucketpath in self._bucketpaths():
            for pk in os.listdir(bucketpath):
                epath = os.path.join(bucketpath, pk)
                if os.path.isfile(epath):
                    yield epath
             
    def write(self, pk, data):
        assert isinstance(pk, int), "Not an integer"
        bp = self._bucket_path_from_pk(pk)
        os.makedirs(bp, exist_ok=True)
        path = os.path.join(bp, str(pk))
        with open(path, 'w') as f:
            f.write(data)
        
    def read(self, pk):
        assert isinstance(pk, int), "Not an integer"
        with open(self.path(pk), 'r') as f:
            o = f.read()
        return o

    def delete(self, pk):
        assert isinstance(pk, int), "Not an integer"
        os.remove(self.path(pk))   
    
    def clear(self):
        shutil.rmtree(self._path)

    def size(self):
        return sum(1 for _ in self.paths_read_all())

    def disk_storage_size(self):
        '''
        size in bytes of records.
        '''
        return sum(os.path.getsize(path) for path in self.paths_read_all())
