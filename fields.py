from django.db import models 
from .storage import BucketDBStorage
from django.db.models import signals
from django.core import checks

        
class BucketDBFileField(models.FileField):
    '''
    A file field to use the BucketDB.
    A handful of differences to Django FileField:
    - Uses the BucketDBStorage persistent storage IO
    - Adds an argument 'collection' (and removes 'upload_to')
    - Tests for the 'collection' attribute
    - (optionally) hardwires to the signal 'post_delete', which will
    remove files on delete.
    Django removed the auto-delete from FileField, a decision
    I understand, endorse, and have re-activated.
    '''
    def __init__(self, verbose_name=None, name=None, collection='', 
        storage=None,
        auto_delete=True,
        **kwargs
        ):
        self.auto_delete=auto_delete
        super().__init__(
          verbose_name=verbose_name, 
          name=name, 
          upload_to=collection, 
          storage = BucketDBStorage(), 
          **kwargs
          )

    def check(self, **kwargs):
        # It's a Field, can use Field's buitin check framework.
        errors = super().check(**kwargs)
        errors.extend(self._check_upload_to_exists())
        return errors
        
    def _check_upload_to_exists(self):
        if not self.upload_to:
            return [
                checks.Error(
                    "'collection' must be declared.",
                    hint=("Set a name for the 'collection' on the field "
                          "(the BucketDB can handle multiple sub-collections)."),
                    obj=self,
                    id='filemanager.C001',
                )
            ]
        else:
            return []

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        # Only run delete on non-abstract models when auto_deleting
        if not cls._meta.abstract and self.auto_delete:
            signals.post_delete.connect(self.post_delete, sender=cls)
            
    # delete is not called automatically, so we must use the signal
    # (annoying R.C.)
    def post_delete(self, instance, *args, **kwargs):
        self.storage.delete(instance.path)
        
