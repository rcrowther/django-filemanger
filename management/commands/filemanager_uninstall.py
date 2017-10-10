from django.core.management.base import BaseCommand, CommandError
from filemanager.models import Effect, Pipe, PipeEffect, File
from django.db import connection



class Command(BaseCommand):
    help = 'Uninstall the filemanager app database tables, with further instructions'

    def drop(self, dbname):
        _DropSQL = "DROP TABLE {}"

        c = connection.cursor()
        try:
            c.execute(_DropSQL.format(dbname))
        finally:
            c.close()
            
    def handle(self, *args, **options):
        self.drop(Effect._meta.db_table) 
        self.drop(Pipe._meta.db_table)
        self.drop(PipeEffect._meta.db_table)
        self.drop(File._meta.db_table)
        self.stdout.write(self.style.SUCCESS('Uninstalled the filemanager app database tables'))
        self.stdout.write('You will need also to:')
        self.stdout.write(' - remove app registration in settings.py')
        self.stdout.write(' - remove use of taxonomy fields in the forms in other applications')
        self.stdout.write(' - remove use of taxonomy methods in templates or views')
        self.stdout.write('and, optionally:')
        self.stdout.write(' - remove sitewide URLs in url.py')
        self.stdout.write(' - remove the folders and files')
