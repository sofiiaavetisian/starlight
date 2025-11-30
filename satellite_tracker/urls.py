"""
URL configuration for satellite_tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from satellite_tracker.health import health_status
from satellites.views import (
    catalog,
    catalog_search,
    favorite_add,
    favorite_remove,
    favorites_list,
    home,
    satellite_detail,
    SignUpView,
)

# URL patterns for the satellite_tracker project
urlpatterns = [
    path('admin/', admin.site.urls), # admin interface
    path('', home, name='home'), # homepage
    path('catalog/', catalog, name='catalog'), # satellite catalog
    path('catalog/search/', catalog_search, name='catalog-search'), # search in catalog
    path('catalog/<int:norad_id>/', satellite_detail, name='satellite-detail'), # satellite detailed view
    path('favorites/', favorites_list, name='favorites'), # list of favorite satellites
    path('favorites/add/<int:norad_id>/', favorite_add, name='favorite-add'), # add to favorites
    path('favorites/remove/<int:norad_id>/', favorite_remove, name='favorite-remove'), # remove from favorites
    path('accounts/signup/', SignUpView.as_view(), name='signup'), # user signup
    path('accounts/', include('django.contrib.auth.urls')), # authentication (login/logout)
    path('api/', include('satellites.urls')),  # API endpoints
    path('health/', health_status, name='health'),  # simple health probe
    path('', include('django_prometheus.urls')),  # /metrics endpoint
]
