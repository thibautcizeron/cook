from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy


urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('account/', views.user_account, name='account'),
    path('account_edit/', views.user_account_edit, name='account_edit'),
    path('account_delete/', views.user_account_delete, name='account_delete'), 

    path("users_list/", views.user_list, name="users_list"),
    path("search_users/", views.search_users, name="search_users"),

    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='auth/password_reset/reset.html',
             email_template_name='auth/password_reset/reset_email.html',
             subject_template_name='auth/password_reset/reset_subject.txt',
             success_url=reverse_lazy('reset_done')
         ), 
         name='reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='auth/password_reset/reset_done.html'
         ), 
         name='reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='auth/password_reset/reset_confirm.html',
             success_url=reverse_lazy('reset_complete')
         ), 
         name='reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='auth/password_reset/reset_complete.html'
         ), 
         name='reset_complete'),

    path('politique/', views.show_politique, name='politique'),
    path('mentions/', views.show_mentions, name='mentions'),
    path('contact/', views.contact, name='contact'),
]