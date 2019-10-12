from django.urls import path

from rest_framework.authtoken.views import obtain_auth_token

from api import views

urlpatterns = [
    path('account/', views.account_details),
    path('create-account/', views.create_account),
    path('families/', views.ListFamily.as_view()),
    path('families/<int:pk>/', views.DetailFamily.as_view()),
    path('families/of-individual/<int:pk>/', views.list_family_of_individual),
    path('families/search/<str:pattern>/', views.search_families),
    path('ping/', views.ping),
    path('individuals/', views.ListIndividual.as_view()),
    path('individuals/<int:pk>/', views.DetailIndividual.as_view()),
    path('individuals/<int:pk>/verbose', views.verbose_individual_detail),
    path('individuals/<int:pk>/ancestors', views.individual_ancestors),
    path('individuals/<int:pk>/descendants', views.individual_desendants),
    path('login/', obtain_auth_token),
    path('logout/', views.logout),
    path('search-individuals/<str:pattern>', views.search_individuals),
]
