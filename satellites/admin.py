from django.contrib import admin

from .models import TLE, Favorite

#my models to be registered in the admin interface
admin.site.register(TLE)
admin.site.register(Favorite)
