from django.contrib import admin
from .models import Research

@admin.register(Research)
class ResearchAdmin(admin.ModelAdmin):
    list_display = ('id', 'query', 'status', 'model', 'created_at')
    list_filter = ('status', 'model')
    search_fields = ('id', 'query')
    readonly_fields = ('id', 'created_at', 'updated_at') 