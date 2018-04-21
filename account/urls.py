from django.urls import path
from . import views

urlpatterns = [
    path('account', views.account, name='account'),
    path('funds/<int:pk>', views.funds, name='funds'),
    path('funds/<int:pk>/edit', views.edit_funds, name='edit_funds'),
    path('funds/<int:pk>/delete', views.delete_funds, name='delete_funds'),
    path('funds/new', views.new_funds, name='new_funds'),
    path('funds', views.myfunds, name='myfunds'),
    path('history', views.history, name='history'),
    path('notifications', views.notifications, name='notifications'),
    path('notify_back', views.notify_back, name='notify_back'),
    # Json response
    path('notify', views.notify, name='notify'),
    path('new_notify', views.new_notify, name='new_notify'),
    path('accounts', views.accounts, name='accounts')
]
