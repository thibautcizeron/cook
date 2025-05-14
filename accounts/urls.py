from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('login/', views.user_login, name='users_login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='users_register'),
    path('users_account/', views.user_account, name='users_account'),
    path('users_account_edit/', views.user_account_edit, name='users_account_edit'),

    path("users/", views.user_list, name="users"),
    path("search-users/", views.search_users, name="search_users"),

    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url='/accounts/password-reset/done/'
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/accounts/password-reset-complete/'
         ), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),

    path('politique/', views.show_politique, name='politique'),
    path('mentions/', views.show_mentions, name='mentions'),
]
