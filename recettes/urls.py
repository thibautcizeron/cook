from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [

    path('home/', views.home, name='layout'),

    path('recettes/', views.recettes_list, name='recettes'),
    path('recettes/<int:recette_id>/', views.recettes_details, name='recettes_details'),
    path('recettes/recettes_add/', views.recettes_add, name='recettes_add'),
    path('recettes/<int:pk>/edit/', views.recettes_edit, name='recettes_edit'),
    path('recettes/<int:pk>/delete/', views.recettes_delete, name='recettes_delete'),

    path('search_recipe/', views.search_recipe, name='search_recipe'),
    path('search_recettes/', views.search_recettes, name='search_recettes'),

    path('ingredients/', views.ingredient_list, name='ingredients'),
    path('ingredients/ingredients_add/', views.ingredients_add, name='ingredients_add'),
    path('ingredients/<int:pk>/edit/', views.ingredients_edit, name='ingredients_edit'),
    path('ingredients/<int:pk>/delete/', views.ingredients_delete, name='ingredients_delete'),

    path('entrees/', views.show_starts, name='layout_starts'),
    path('plats/', views.show_dishes, name='layout_dishes'),
    path('desserts/', views.show_desserts, name='layout_desserts'),
    path('cocktails/', views.show_cocktails, name='layout_cocktails'),

    path('', views.loading_page, name='loading_page'),
    path('recettes/<int:recette_id>/noter/', views.noter_recette, name='noter_recette'),

]
