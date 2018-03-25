from django.urls import path
from . import views

urlpatterns = [
    path('account', views.account, name='account'),
    path('funds/<int:pk>', views.funds, name='funds'),
    path('funds/<int:pk>/edit', views.edit_funds, name='edit_funds'),
    path('funds/new', views.new_funds, name='edit_funds'),
    path('funds', views.myfunds, name='myfunds'),
    path('history', views.history, name='history'),
    path('accounts', views.accounts, name='accounts')
]
