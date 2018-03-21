from need.models import ModelNeed
from need.fields import IdField, TextField, DateTimeField
from need.managers import ManagerManager
from .models import File

class FileNeed(ModelNeed):
   name=TextField(stored=True, field_boost=2.0)
   description=TextField(stored=True)
   date=DateTimeField()
   author=IdField(stored=True)
   #! undecided form, as yet
   #lcns=IdField(stored=True)
   manager = ManagerManager()
   class Meta:
     #need_index = 'file'
     model=File
     fields = ['name', 'description', 'date', 'author']
