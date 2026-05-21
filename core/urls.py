from django.urls import path
from .views import plans_page, tasks_page

urlpatterns = [
    path("tasks/", tasks_page, name="tasks_page"),
    path("plans/", plans_page, name="plans_page"),
]
