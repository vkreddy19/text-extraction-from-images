from django.urls import path

from . import views

urlpatterns = [
    # path('', views.index, name='index'),
    path('', views.upload_file, name='home'),
    path('burials', views.BurialsListView.as_view(), name='burials'),
    path('multi', views.FileFieldView.as_view(), name='multi'),
    path('image/<file>/', views.my_image, name='images'),
    path('export', views.export_to_csv, name='export')
]

