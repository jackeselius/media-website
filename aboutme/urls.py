# accounts/urls.py
from django.urls import path
from .views import aboutme, Jack_Eselius, Gage_Condon, Diksha_Thach, Kate_Eselius
#from .views import Personal_Resume  #could eventually do something like this where its generic person and it grabs the resume info 
#but for now doing this so I can give out direct links to pages with names like/Jack_Eselius.com for example


urlpatterns = [

    # path("aboutme/", aboutme, name="aboutme"),
    path("aboutme/", aboutme, name="aboutme"),
    path("Jack_Eselius/", Jack_Eselius, name="Jack_Eselius"),
    path("Gage_Condon/", Gage_Condon, name="Gage_Condon"),
    path("Diksha_Thach/", Diksha_Thach, name="Diksha_Thach"),
    path("Kate_Eselius/", Kate_Eselius, name="Kate_Eselius"),


    
]
