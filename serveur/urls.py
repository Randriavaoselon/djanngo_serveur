
from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html')),#
    path('api/active-clients/', views.get_active_clients, name='active_clients'),
    path('video_feed/', views.client_video_feed, name='video_feed'),
    path('api/client-count/', views.client_count, name='client-count'),
    path('active-client-count/', views.get_active_client_count, name='active-client-count'),
    path('recent-connections/', views.get_recent_connections, name='recent-connections'),
    path('api/clients/', views.get_all_clients, name='get_all_clients'),
    path('api/clients/<int:client_id>/', views.update_client_info, name='update_client_info'),
    path('api/clients_delete/<int:client_id>/', views.delete_client, name='delete_client'),
    # path('client-screenshots/<int:client_id>/', views.get_client_screenshots, name='client_screenshots'),

    path('client-screenshots/<int:client_id>/', views.get_client_screenshots, name='get_client_screenshots'),
    path('delete-client-screenshots/<int:client_id>/', views.delete_client_screenshots, name='delete_client_screenshots'),
    path('api/get-directory-content/', views.get_directory_content, name='get_directory_content'),


   
    path('video-feed/', views.client_video_feed, name='client_video_feed'),
    path('active-clients/', views.get_active_clients, name='get_active_clients'),
    path('all-clients/', views.get_all_clients, name='get_all_clients'),


]


