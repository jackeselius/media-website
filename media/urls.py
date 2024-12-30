# accounts/urls.py
from django.urls import path

from media import views


urlpatterns = [
    path("upload/", views.upload, name="upload"),
    path("files/", views.file_list, name="file_list"),
    path("files/<int:pk>/", views.delete_file, name="delete_file"),
    #path("videos/", views.video_list, name="video_list"),
    #path("videos/upload", views.upload_video, name="upload_video"),
    #path("images/", views.image_list.as_view(), name="image_list"),  #done as a class in views while the rest were done as functions
    #path("images/upload", views.upload_image, name="upload_image"),



]
