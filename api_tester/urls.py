from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('profiles/', views.profiles, name='profiles'),
    path('profiles/create/', views.create_profile, name='create_profile'),
    path('profiles/<int:profile_id>/edit/', views.edit_profile, name='edit_profile'),
    path('profiles/<int:profile_id>/delete/', views.delete_profile, name='delete_profile'),
    path('test-endpoints/', views.test_endpoints, name='test_endpoints'),
    path('test-runs/', views.test_runs, name='test_runs'),
    path('test-runs/<int:test_run_id>/', views.test_run_detail, name='test_run_detail'),
    path('test-results/<int:result_id>/', views.test_result_detail, name='test_result_detail'),
    path('endpoints/', views.endpoints, name='endpoints'),
    path('import-endpoints/', views.import_api_endpoints, name='import_api_endpoints'),
    path('endpoints/test/', views.test_endpoint, name='test_endpoint'),
    path('servers/', views.servers, name='servers'),
    path('servers/create/', views.create_server, name='create_server'),
    path('servers/<int:server_id>/', views.server_detail, name='server_detail'),
    path('servers/<int:server_id>/toggle-status/', views.toggle_server_status, name='toggle_server_status'),
    path('profiles/export/', views.export_profiles, name='export_profiles'),
    path('profiles/import/', views.import_profiles, name='import_profiles'),
] 