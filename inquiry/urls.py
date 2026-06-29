from django.urls import path

from . import views

app_name = "inquiry"

urlpatterns = [
    path("", views.home, name="home"),

    path("manage/", views.manage_records, name="manage_records"),
    path("manage/quick-inquiry/", views.quick_inquiry, name="quick_inquiry"),
    path("manage/settings/", views.inquiry_settings, name="inquiry_settings"),
    path("manage/create/", views.record_create, name="record_create"),
    path("manage/<int:pk>/edit/", views.record_update, name="record_update"),
    path("manage/<int:pk>/delete/", views.record_delete, name="record_delete"),
    path("manage/import/", views.import_excel, name="import_excel"),
    path("manage/logs/", views.inquiry_logs, name="inquiry_logs"),
]
