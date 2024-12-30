from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
import os
from pathlib import Path
from .forms import FileForm
from .models import File
from django.views.generic import TemplateView, ListView

# Create your views here.
basedirectory = Path(__file__).resolve().parent.parent

def upload(request):
    if request.method == 'POST':
        form = FileForm(request.user, request.POST, request.FILES)  #POST has attribnutes of video form also request has user attribute as well

        if form.is_valid():
            #formUpdated = form.save(commit = False)    #USE THIS if you dont want the ujploader to be able to change the prewritten owner field
            #formUpdated.owner = request.user
            #formUpdated.save()
            #form.save_m2m() #MIGHT NEED THIS NOT SURE
            #print(request.user)
            form.save() #USE this if you want the uploader to be able to save the file to someone elses drive too
            return redirect('file_list')
    else: #if request is GET
        form = FileForm(request.user)
    return render(request, 'mediaTemplates/upload.html', {
        'form': form   #allows for us to put a form in the upload_video.html
    }) #http://68.162.213.6:4774/media/videos/upload

def file_list(request):
    #print("FILE LIST VIEW ACTIVATED")
    files = File.objects.all()
    return render(request, 'mediaTemplates/file_list.html', {
        'files' : files
    })

def delete_file(request, pk):
    print("DELETE VIEW METHOD CALLED")
    #if request.method == 'POST':
    file = File.objects.get(pk=pk)
    file.delete()
    print("DELETE VIEW METHOD CALLED 22222")

    return redirect('file_list')
#def delete_file(request, pk):
    #f = File.objects.get(pk=pk)
    #fs = FileSystemStorage()
    #fs.delete(f.file)
    #f.delete()



#beta
#VIDEOS
# def video_list(request):
#     videos = Video.objects.all()
#     return render(request, 'mediaTemplates/video_list.html', {
#         'videos' : videos
#     }) #http://68.162.213.6:4774/media/videos/

# def upload_video(request):
#     if request.method == 'POST':
#         form = VideoForm(request.user, request.POST, request.FILES)  #POST has attribnutes of video form also request has user attribute as well

#         if form.is_valid():
#             #formUpdated = form.save(commit = False)    #USE THIS if you dont want the ujploader to be able to change the prewritten owner field
#             #formUpdated.owner = request.user
#             #formUpdated.save()
#             #form.save_m2m() #MIGHT NEED THIS NOT SURE
#             #print(request.user)
#             form.save() #USE this if you want the uploader to be able to save the file to someone elses drive too
#             return redirect('video_list')
#     else: #if request is GET
#         form = VideoForm(request.user)
#     return render(request, 'mediaTemplates/upload_video.html', {
#         'form': form   #allows for us to put a form in the upload_video.html
#     }) #http://68.162.213.6:4774/media/videos/upload

# #CLASS EXAMPLE INSTEAD OF FUNCTION
# #uses packages from ccbv.uk.co
# class image_list(ListView):  #uses the import of ListView
#     model = Image
#     template_name = 'mediaTemplates/image_list.html'
#     context_object_name = 'images'

# def upload_image(request):
#     if request.method == 'POST':
#         form = ImageForm(request.user, request.POST, request.FILES)  #POST has attribnutes of video form also request has user attribute as well

#         if form.is_valid():
#             #formUpdated = form.save(commit = False)    #USE THIS if you dont want the ujploader to be able to change the prewritten owner field
#             #formUpdated.owner = request.user
#             #formUpdated.save()
#             #form.save_m2m() #MIGHT NEED THIS NOT SURE
#             #print(request.user)
#             form.save() #USE this if you want the uploader to be able to save the file to someone elses drive too
#             return redirect('image_list')
#     else: #if request is GET
#         form = ImageForm(request.user)
#     return render(request, 'mediaTemplates/upload_image.html', {
#         'form': form   #allows for us to put a form in the upload_video.html
#     })
