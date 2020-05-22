from django.contrib import admin

from reporting import models


@admin.register(models.Report)
class ReportAdmin(admin.ModelAdmin):
    pass
