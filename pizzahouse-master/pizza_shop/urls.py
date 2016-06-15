from django.conf.urls import url
from pizza_shop import views

urlpatterns = [
    url(r'^$', views.index, name='main'),

    url(r'^accounts/login/$', views.login_user, name='login'),
    url(r'^accounts/logout/$', views.logout_user, name='logout'),
    url(r'^accounts/register/', views.register, name='register'),
    url(r'^accounts/profile/$', views.account, name='account'),
    url(r'^accounts/order/$', views.get_order, name='order'),
    url(r'^accounts/', views.account, name='account'),

    url(r'^about/$', views.about, name='about'),

    url(r'^handler/$', views.ajax_handler, name='handler'),

    url(r'^(?P<link>[0-9a-zA-Z_-]*)/$', views.section, name='section'),
    url(r'^(?P<link>[0-9a-zA-Z_-]*)/(?P<sublink>[0-9a-zA-Z_-]*)/$', views.subsection, name='subsection'),
    url(r'^(?P<link>[0-9a-zA-Z_-]*)/(?P<sublink>[0-9a-zA-Z_-]*)/(?P<meal_link>[0-9a-zA-Z_-]*)/$',
        views.meal, name='meal'),
]
