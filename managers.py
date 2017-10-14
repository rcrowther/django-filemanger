from whoosh import fields, index
#from whoosh.filedb import filestore
from whoosh.index import open_dir
from whoosh.qparser import QueryParser

import time


class BaseManager:    
    def __init__(self, whoosh_base, whoosh_index, whoosh_schema):
        self._whoosh_base = whoosh_base
        self._whoosh_index = whoosh_index
        self._whoosh_schema = whoosh_schema
        self.model = None
        self.name = None
        
    #def add_model_data(self, model):
    #    self.model = model


#! change schema?
#! file locked version
#! async version
#! fuzzy search
#!stem search
class Manager(BaseManager):
    '''
    A basic Whoosh manager.
    Every operation is self contained, and tidies after the action.
    The operations are blocking.
    '''
    def __init__(self, whoosh_base, whoosh_index, whoosh_schema):
        super().__init__(whoosh_base, whoosh_index, whoosh_schema)

    def bulk_add(self, it):
        start = time.time()
        ix = open_dir(self._whoosh_base, self._whoosh_index)
        end = time.time()
        print('opendir', 'took', str(end - start), 'time')
        start = time.time()
        writer = ix.writer()
        end = time.time()
        print('writer', 'took', str(end - start), 'time')
        for e in it:
            writer.add_document(e)
        writer.commit()      
        ix.close()

    def add(self, **fields):
        '''
        Write a document.
        Ignores keys not in schema. No data for unprovided schema keys.
        
        @param fields keys for the schema, values for values. 
        '''
        start = time.time()
        ix = open_dir(self._whoosh_base, self._whoosh_index)
        end = time.time()
        print('opendir', ' took', str(end - start), 'time')
        start = time.time()
        writer = ix.writer()
        end = time.time()
        print('writer', ' took', str(end - start), 'time')
        writer.add_document(**fields)
        start = time.time()
        writer.commit()
        end = time.time()
        print('comit', ' took', str(end - start), 'time')
        ix.close()

    def clear(self):
        '''
        Empty the index.
        '''
        ix = open_dir(self._whoosh_base, self._whoosh_index)
        #On fileStorage and RAMStorage, clean()
        # Storage. Can only do on Filestorage.
        #ix.storage.destroy()
        ix.storage.clean()    
        ix.close()

    def delete(self, fieldname, text):
        '''
        Delete a document.
        Match on any key.
        
        @param fieldname key to match against
        @param text match value. 
        '''
        ix = open_dir(self._whoosh_base, self._whoosh_index)
        writer = ix.writer()
        writer.delete_by_term(fieldname, text, searcher=None)
        writer.commit() 
        ix.close()        

    def merge(self, **fields):
        '''
        Merge a document.
        Ignores keys not in schema. No data for unprovided schema keys.
        Checks for unique keys then matches against parameters.
        Slower than add(). Will create if entry does not exist.
        
        @param fields keys for the schema, values for values. 
        '''
        # "It is safe to use ``update_document`` in place of ``add_document``; if
        # there is no existing document to replace, it simply does an add."
        ix = open_dir(self._whoosh_base, self._whoosh_index)
        writer = ix.writer()
        writer.update_document(**fields)
        writer.commit() 
        ix.close()


    def read(self, query, callback):
        start = time.time()
        end = time.time()
        print('opendir', ' took', str(end - start), 'time')
        ix = open_dir(self._whoosh_base, self._whoosh_index)
        r = None
        with ix.searcher() as searcher:
            start = time.time()
            query = QueryParser("author", self._whoosh_schema).parse(query)
            #query = QueryParser("author", ix.schema).parse(query)
            #query = QueryParser("author").parse(query)
            end = time.time()
            print('query', ' took', str(end - start), 'time')
            callback(searcher.search(query))
        ix.close()

    def size(self):
        ix = open_dir(self._whoosh_base, self._whoosh_index)
        r = ix.doc_count()
        ix.close()
        return r
    
    def optimize(self):
        ix = open_dir(self._whoosh_base, self._whoosh_index)
        ix.optimize()
        ix.close()
        
