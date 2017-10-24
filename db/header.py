from struct import Struct, calcsize
import os

DEFAULT_BUCKET_SIZE = 125

_INT_SIZE = calcsize("!i")

_int_struct = Struct("!i")
_uint_struct = Struct("!I")
pack_int = _int_struct.pack
pack_uint = _uint_struct.pack
unpack_int = _int_struct.unpack
unpack_uint = _uint_struct.unpack
       
            

class Header():
    def __init__(self, path):
        self.path = path
        self._last_id = None
        self._bucket_size = None
        self._size = None
        self._is_binary = False
                
    def _read(self, pos):
        with open(self.path, 'rb+') as f:
            f.seek(pos * _INT_SIZE)
            data = unpack_int(f.read[_INT_SIZE])
        return data[0]

    def _write(self, pos, data):
        with open(self.path, 'rb+') as f:
            f.seek(pos * _INT_SIZE)
            f.write(pack_int(data))

    def _set_all(self, last_id, bucket_size, size, is_binary):
        with open(self.path, 'wb+') as f:
            f.write(pack_int(last_id))
            f.write(pack_int(bucket_size))
            f.write(pack_int(size))
            f.write(pack_int(1 if is_binary else 0))
            self._last_id = last_id
            self._bucket_size = bucket_size
            self._size = size
            self._is_binary = is_binary
                  
    def clear(self):
        self._set_all(-1, 255, 0, False)
                    
    def create(self, last_id=-1, bucket_size=DEFAULT_BUCKET_SIZE, size=0, is_binary=False):
        if os.path.exists(self.path):
            raise Exception('header "{}" requested but exists'.format(
                self.path
            ))
        self._set_all(last_id, bucket_size, size, is_binary)

            
    def load(self):
        if (not os.path.exists(self.path)):
            # don't try to ride this, in case of accidental deletion
            print('ow')
            raise FileNotFoundError('missing header file for physical database: looked in {0}'.format(
                self.path
                ))
        with open(self.path, 'rb+') as f:
            self._last_id = unpack_int(f.read(_INT_SIZE))[0]
            self._bucket_size = unpack_int(f.read(_INT_SIZE))[0]
            self._size = unpack_int(f.read(_INT_SIZE))[0]
            self._is_binary = (1 == unpack_int(f.read(_INT_SIZE))[0])
       
    def _set_last_id(self, data):
        self._write(0, data)
        self._last_id = data

    def _get_last_id(self):
        return self._last_id

    def next_id(self):
        '''
        Get the next id in the auto increment seq.
        The policy is 'call next_id() then query for last_id', with
        the id starting from -1. 
        '''
        new_id = self._last_id + 1
        self._set_last_id(new_id)
        return new_id

    def _set_bucket_size(self, data):
        self._write(1, data)
        self._bucket_size = data

    def _get_bucket_size(self):
        return self._bucket_size
              
    def _set_size(self, data):
        self._write(2, data)
        self._size = data

    def _get_size(self):
        return self._size     

    def size_inc(self):
        new_size = self._size + 1
        self._set_size(new_size)
        
    def size_dec(self):
        new_size = self._size - 1
        self._set_size(new_size)
        
    def _set_is_binary(self, data):
        self._write(3, 1 if data else 0)
        self._is_binary = data

    def _get_is_binary(self):
        return self._is_binary 
                   
    last_id = property(_get_last_id, _set_last_id)
    bucket_size = property(_get_bucket_size, _set_bucket_size)
    size = property(_get_size, _set_size)
    is_binary = property(_get_is_binary, _set_is_binary)

    def __repr__(self):
        return '{0}-{1}-{2}-{3}'.format(
            self._last_id,
            self._bucket_size,
            self._size,
            self._is_binary
        )
