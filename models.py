from django.db import models



class Effect(models.Model):
    name = models.CharField(
      max_length=255,
      db_index=True,
      unique=True,
      help_text="Name for an effect. Limited to 255 characters.",
      )
      
    description = models.CharField(
      max_length=255,
      blank=True,
      default='',
      help_text="Overall description of an effect. Limited to 255 characters.",
      )
      
    def __str__(self):
      return "{0}".format(
      self.name, 
      )
      
class Pipe(models.Model):
    name = models.CharField(
      max_length=255,
      db_index=True,
      unique=True,
      help_text="Name for a series of effects. Limited to 255 characters.",
      )
      
    description = models.CharField(
      max_length=255,
      blank=True,
      default='',
      help_text="Overall description of a series of effects. Limited to 255 characters.",
      )

    def __str__(self):
      return "{0}".format(
      self.name, 
      )

      
class PipeEffectManager(models.Manager):
    pass


    
class PipeEffect(models.Model):
    pipe = models.ForeignKey(
      Pipe,
      db_index=True,
      on_delete=models.CASCADE,
      help_text="Pipe with associated effects.",
      )

    idx = models.IntegerField(
      db_index=True,
      help_text="Position of this effect in a pipe.",
      )
            
    effect = models.ForeignKey(
      Effect,
      db_index=True,
      on_delete=models.CASCADE,
      help_text="Effect in a pipe",
      )

    objects = models.Manager()
    system = PipeEffectManager()



class FileManager(models.Manager):
    pass    
    
    
class File(models.Model):
    name = models.CharField(
      max_length=255,
      db_index=True,
      unique=True,
      help_text="Name for this file. Limited to 255 characters.",
      )

    description = models.CharField(
      max_length=255,
      blank=True,
      default='',
      help_text="Description of the category. Limited to 255 characters.",
      )
      
    # uneditable, visible
    date = models.DateTimeField(
      'date inserted.', 
      auto_now_add=True
      )
    
    # uneditable, visible
    mod_date = models.DateTimeField(
      'date last modified.',
      auto_now_add=True
      )
    
    #path = models.CharField(
    #  max_length=256,
    path = models.FileField(
      #upload_to='uploads/',
      #unique=True,
      help_text="Path to file.",
      )
      
    author = models.CharField(
      max_length=64,
      blank=True, 
      default='',
      help_text="Name of the author/source.",
      )
      
    size = models.IntegerField(
      help_text="Size of this file in KB.",
      )
       
    lcns = models.CharField(
      max_length=64,
      blank=True, 
      default='',
      help_text="Licence on the file.",
      )
     
    objects = models.Manager()
    system = FileManager()

    def __str__(self):
      return "{0}".format(
      self.name, 
      )


class BucketFile(models.Model):
    bucket = models.IntegerField(
      help_text="Index of physical location of a file.",
      )
      
    f = models.ForeignKey(
      File,
      verbose_name="file",
      on_delete=models.CASCADE,
      help_text="File with a location.",
      )

