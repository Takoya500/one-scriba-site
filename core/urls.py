from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('pricing/', views.pricing, name='pricing'),
    path('magazine/', views.magazine, name='magazine'),
    path('autori/', views.autori, name='autori'),
    path('autori/<int:id>/', views.autore, name='autore'),
    path('festival/', views.festival, name='festival'),
    path('affiliazioni/', views.affiliazioni, name='affiliazioni'),
    path('about/', views.learn_more, name='about'),
    path('learn-more/', views.learn_more, name='learn_more'),
    path('download/', views.download, name='download'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('contact/', views.contact, name='contact'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('api/desktop-login/', views.desktop_login_view, name='desktop_login'),
    path('api/check-subscription/', views.check_subscription_view, name='check_subscription'),
    path('api/lemonsqueezy/webhook/', views.lemonsqueezy_webhook, name='lemonsqueezy_webhook'),
]
