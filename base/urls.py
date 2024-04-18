from django.urls import path 
from . import views 
  
urlpatterns = [ 
    path("", views.home, name="home"), 
    path("learn/", views.learn, name="learn"), 
    path("practice/", views.practice, name="practice"), 
    path("statistics/", views.statistics, name="statistics"),
    path('signin/',views.signin, name='signin'),
    path('signout/',views.signout, name='signout'),
    path('signup/',views.signup, name='signup'),
    path('practice/update', views.practice_update, name='update'),
    path('practice/playsong', views.periodic_update_entire_range, name='playsong'),
    path('practice/process', views.audio_processing, name='process_audio'),
]

