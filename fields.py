from django.db import models 
from .storage import BucketDBStorage
from django.db.models import signals

        
class BucketDBFileField(models.FileField):
    '''
    A file field to use the BucketDB.
    A handful of differences to Django FileField:
    - Uses the BucketDBStorage persistent storage IO
    - Adds an attribute 'collection' (and removes 'upload_to')
    - Tests for the 'collection' attribute
    - (optionally) hardwires to the signal 'post_delete', which will
    remove files on delete.
    Django removed the auto-delete from FileField, a decision
    I understand, endorse, and have re-activated.
    '''
    def __init__(self, verbose_name=None, name=None, upload_to='', storage=None, **kwargs):
        super().__init__(
          verbose_name=verbose_name, 
          name=name, 
          upload_to=upload_to, 
          storage = BucketDBStorage(), 
          **kwargs
          )
          
        #print("post delete field dict (init)!: \n" + str(self.__dict__))
        #print("post delete field (init)!: " + self.__str__())
        #post_delete.connect(self.post_delete, self.model, 'filemanager-field-delete')

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        # Only run delete on non-abstract models
        if not cls._meta.abstract:
            signals.post_delete.connect(self.post_delete, sender=cls)
            
    # delete is not called automatically, so we must use the signal
    # (annoying R.C.)
    def post_delete(self, instance, *args, **kwargs):
        self.storage.delete(instance.path)
        
