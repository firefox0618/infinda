from django.urls import path

from .views import CurrentSubscriptionView


urlpatterns = [
    path("", CurrentSubscriptionView.as_view(), name="subscription-current"),
]
