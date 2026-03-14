from django.contrib import admin

from .models import Game


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('id', 'player_one', 'player_two', 'status', 'winner', 'created_at')
    list_filter = ('status',)
    raw_id_fields = ('player_one', 'player_two', 'winner')
