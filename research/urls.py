from django.urls import path
from . import views

urlpatterns = [
    path('', views.api_root, name='api_root'),
    path('research', views.start_research, name='start_research'),
    path('research/<str:research_id>', views.get_research, name='get_research'),
    path('research/<str:research_id>/stream', views.stream_research, name='stream_research'),
    path('models', views.get_models, name='get_models'),
    path('search-providers', views.get_search_providers, name='get_search_providers'),
] 