from django.contrib import admin
from .models import Conversation, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('timestamp', 'role', 'content')
    can_delete = False

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'created_at')
    search_fields = ('user__username', 'title')
    list_filter = ('created_at', 'user')
    inlines = [MessageInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_user', 'role', 'short_content', 'timestamp')
    search_fields = ('content', 'conversation__user__username')
    list_filter = ('role', 'timestamp', 'conversation__user')
    
    def get_user(self, obj):
        return obj.conversation.user.username
    get_user.short_description = 'User'
    get_user.admin_order_field = 'conversation__user__username'
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'
