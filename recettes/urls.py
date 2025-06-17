from django.urls import path
from . import views

urlpatterns = [

    path('home/', views.home, name='layout'),
    path('recettes/', views.recettes_list, name='recipes_list'),
    path('recettes/<int:recette_id>/', views.recettes_details, name='recipe_details'),
    path('recettes/recettes_add/', views.recettes_add, name='recipe_add'),
    path('recettes/<int:pk>/edit/', views.recettes_edit, name='recipe_edit'),
    path('recettes/<int:pk>/delete/', views.recettes_delete, name='recipe_delete'),
    path('ingredients/', views.ingredient_list, name='ingredients_list'),
    path('ingredients/ingredients_add/', views.ingredients_add, name='ingredient_add'),
    path('ingredients/<int:pk>/edit/', views.ingredients_edit, name='ingredient_edit'),
    path('ingredients/<int:pk>/delete/', views.ingredients_delete, name='ingredient_delete'),
    path('entrees/', views.show_starts, name='layout_starts'),
    path('plats/', views.show_dishes, name='layout_dishes'),
    path('desserts/', views.show_desserts, name='layout_desserts'),
    path('cocktails/', views.show_cocktails, name='layout_cocktails'),
    path('', views.loading_page, name='loading_page'),
    path('recettes/<int:recette_id>/noter/', views.noter_recette, name='noter_recette'),
    path('logs/', views.activity_logs, name='activity_logs'),
    path('logs/<int:log_id>/', views.activity_log_detail, name='activity_log_detail'),

    path('search/', views.search_recipes, name='search_recipes'),
    path('search/advanced/', views.advanced_search, name='advanced_search'),
    path('api/search/', views.search_recipe_api, name='search_recipe_api'),
    
    # Garder l'ancienne route pour la compatibilité (mais rediriger vers search_recipe_api)
    path('search_recipe/', views.search_recipe_api, name='search_recipe'),
    

]
