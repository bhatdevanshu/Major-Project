from django.urls import path
from  plagiarism import views
urlpatterns = [
    path('', views.home),
    path('checker', views.checker),
    path('about', views.about),
    path('contact', views.contact),
    path('results/<file_path>',views.render_result)
]