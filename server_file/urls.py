from django.urls import path
from . import views

urlpatterns = [
    #path('get_file_list/', views.get_file_list, name='get_file_list'),
    path('api/file_list/', views.get_file_list, name='get_file_list'),
    path('api/change_directory/', views.change_directory, name='change_directory'),
]