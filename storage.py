import os
from django.conf import settings
from django.core.files.storage import Storage, FileSystemStorage
from filemanager.db import DB
from django.core.files.move import file_move_safe


# 'upload_to' is Django's way of establishing 'buckets'. From a user 
# point of view it makes sense to use the attribute to target a 
# collection. From a code point of view, BucketDB handles it's buckets 
# auttomatically, so the use of 'upload_to' is a re-purposing.
# Anyway, I decide the user wins, so 'upload_to' represents a collection.
# R.C.
class BucketDBStorage(FileSystemStorage):
    def __init__(self,
        location=settings.UPLOAD_ROOT,  
        base_url=None, 
        file_permissions_mode=None,
        directory_permissions_mode=None
        ):
        self.db = DB(settings.UPLOAD_ROOT)

        super().__init__(
            location,
            base_url,
            file_permissions_mode,
            directory_permissions_mode
            )

    def _save(self, name, content):
            # e.g. name = 'images/takeaway.jpg'
            print('_save name: ' + str(name))
            collection_str = os.path.dirname(name)
            print('collection_str: ' + str(collection_str))
            #print('uoload_to: ' + str(self.upload_to))
            coll = self.db(collection_str)
            path = None
            with coll.auto_create_cb() as full_path:
                print('full_path: ' + str(full_path))
                path = full_path
                # NB: BucketDB does not guarentee the separator (unlike Django) 
                path_segs = full_path.split(os.path.sep)
                path = os.path.join(path_segs[-3], path_segs[-2], path_segs[-1])
                print('relpath: ' + str(path))
                # This file has a file path that we can move.
                if hasattr(content, 'temporary_file_path'):
                    file_move_safe(content.temporary_file_path(), full_path)

                # This is a normal uploadedfile that we can stream.
                else:
                    # This fun binary flag incantation makes os.open throw an
                    # OSError if the file already exists before we open it.
                    flags = (os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                             getattr(os, 'O_BINARY', 0))
                    # The current umask value is masked out by os.open!
                    fd = os.open(full_path, flags, 0o666)
                    _file = None
                    try:
                        #locks.lock(fd, locks.LOCK_EX)
                        for chunk in content.chunks():
                            if _file is None:
                                mode = 'wb' if isinstance(chunk, bytes) else 'wt'
                                _file = os.fdopen(fd, mode)
                            _file.write(chunk)
                    finally:
                        #locks.unlock(fd)
                        if _file is not None:
                            _file.close()
                        else:
                            os.close(fd)
            # The original code returns a name (which is 'upload_to' + 
            # name). We return the relpath (which is 'upload_to' 
            # (collection) + bucket + pk).
            # In the field, the return is dumped on self.name.
            # self.name is used to construct for filepaths, but not in 
            # any other way (it is an id locator for the file). 
            # Replacing with the relpath means attributes like 'size' 
            # work without overriding.
            return path

