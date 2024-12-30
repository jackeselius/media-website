from django.shortcuts import render
from django.http import HttpResponse
from django.views import generic


# Create your views here.
# def Personal_Resume(request):
#     return HttpResponse("Generic Personal Resume of a Person")

# def aboutme(request):
#     return HttpResponse("About Me Menu")

def aboutme(request):
    return render(request, 'aboutme/aboutme_menu.html')


def Jack_Eselius(request):
    return HttpResponse("Jack Eselius")

def Gage_Condon(request):
    return HttpResponse("Gage Condon")

def Diksha_Thach(request):
    return HttpResponse("Diksha Thach")

def Kate_Eselius(request):
    return HttpResponse("Kate Eselius")