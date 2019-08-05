from django.urls import path

from api import views

urlpatterns = [
    path('individuals/', views.ListIndividual.as_view()),
    path('individuals/<int:pk>/', views.DetailIndividual.as_view()),
    path('individuals/<int:pk>/verbose', views.verbose_individual_detail),
    path('families/', views.ListFamily.as_view()),
    path('families/<int:pk>/', views.DetailFamily.as_view()),
    path('families/of-individual/<int:pk>/', views.list_family_of_individual),
]
