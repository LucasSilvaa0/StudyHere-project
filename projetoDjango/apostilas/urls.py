from django.urls import path
from . import views

urlpatterns = [
    path('adicionar_apostilas/', views.adicionar_apostilas, name='adicionar_apostilas'),
    path('apostila/<int:id>/', views.apostila, name='apostila'),
    path('deletar_apostila/<int:id>/', views.deletar_apostila, name='deletar_apostila')
]