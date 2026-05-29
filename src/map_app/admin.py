from django.contrib import admin

from map_app.models import ActivityItem, Location, Tag


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(ActivityItem)
class ActivityItemAdmin(admin.ModelAdmin):
    search_fields = ("name",)
