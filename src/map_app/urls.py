from django.urls import path

from map_app import views
from map_app.video_processing_callback import video_processing_callback_view

app_name = "map_app"

urlpatterns = [
    path("", views.map_view, name="map"),
    path("videos/", views.video_library_view, name="video_library"),
    path("videos/<int:video_id>/short/", views.video_short_detail_view, name="video_short_detail"),
    path("videos/<int:video_id>/", views.video_detail_view, name="video_detail"),
    path("healthz", views.healthz_view, name="healthz"),
    path("api/map/search/", views.map_search_api_view, name="map_search_api"),
    path("api/activities/<int:activity_id>/modal/", views.activity_modal_view, name="activity_modal"),
    path("api/locations/<int:location_id>/modal/", views.location_modal_view, name="location_modal"),
    path("api/video-processing/callback/", video_processing_callback_view, name="video_processing_callback"),
]
