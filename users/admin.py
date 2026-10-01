from django.contrib import admin
from .models import Profile, Workspace, WorkspaceMember, Invitation

# admin.site.register(Profile)
# admin.site.register(Workspace)
# admin.site.register(WorkspaceMember)
# admin.site.register(Invitation)


# Adiciona WorkspaceMember e Invitation no cadastro do Workspace, facilitando o preenchimento de todo o fluxo em apenas uma tela
class WorkspaceMemberInline(admin.TabularInline):
    model = WorkspaceMember
    readonly_fields = ('registered_at',)  


class InvitationInline(admin.TabularInline):
    model = Invitation
    readonly_fields = ('token', 'sent_at')  


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'user__first_name', 'user__last_name', 'telephone')
    search_fields = ('user__username', 'user__email', 'telephone')


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ('holder', 'name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'holder__user__username')
    readonly_fields = ('created_at',)
    inlines = [WorkspaceMemberInline, InvitationInline]  


@admin.register(WorkspaceMember)
class WorkspaceMemberAdmin(admin.ModelAdmin):
    list_display = ('profile', 'workspace', 'role', 'registered_at')
    list_filter = ('role', 'registered_at')
    search_fields = ('profile__user__username', 'workspace__name')
    readonly_fields = ('registered_at',)


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'workspace', 'status', 'sent_at')
    list_filter = ('status', 'sent_at')
    search_fields = ('email', 'workspace__name')
    readonly_fields = ('token', 'sent_at')


