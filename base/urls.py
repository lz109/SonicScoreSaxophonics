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
    path('practice/load_data', views.load_data, name='load_data'),
    path('practice/update', views.practice_update, name='update'),
    path('practice/playsong', views.periodic_update_entire_range, name='playsong'),
    path('practice/process', views.audio_processing, name='process_audio'),
    path('practice/upload_audio/', views.upload_audio, name='upload_audio'),
    path('practice/upload_fingering/', views.upload_fingering, name='upload_fingering'),
    path('practice/integration/', views.integration, name='integration'),
    path('practice/get_feedback/', views.get_feedback, name='get_feedback'),
]

