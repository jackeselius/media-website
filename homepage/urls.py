# accounts/urls.py
from django.urls import path
from .views import home
#from .views import Personal_Resume  #could eventually do something like this where its generic person and it grabs the resume info 
#but for now doing this so I can give out direct links to pages with names like/Jack_Eselius.com for example


urlpatterns = [

    path('', home, name="home"),
    
]
