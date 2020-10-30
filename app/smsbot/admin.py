from django.contrib import admin

from smsbot import models


@admin.register(models.Number)
class NumberAdmin(admin.ModelAdmin):
    list_display = ("phone", "welcome_time", "opt_out_time", "opt_in_time")


@admin.register(models.SMSMessage)
class SMSMessageAdmin(admin.ModelAdmin):
    list_display = ("phone", "created_at", "direction", "message")


@admin.register(models.Blast)
class BlastAdmin(admin.ModelAdmin):
    list_display = ("uuid", "description", "campaign", "blast_type")
