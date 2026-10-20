from django.urls import path
from . import views as views

app_name = "users"

urlpatterns = [
    # Cadastro e Perfil
    path('cadastro/', views.RegisterView.as_view(), name='register'),
    path('perfil/', views.ProfileDetailView.as_view(), name='profile'),
    path('perfil/editar/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('espacos/', views.WorkspaceListView.as_view(), name='workspace_list'),
    path('espacos/novo/', views.WorkspaceCreateView.as_view(), name='workspace_create'),
    path('espacos/<int:pk>/', views.WorkspaceDetailView.as_view(), name='workspace_detail'),
    path('espacos/<int:pk>/selecionar/', views.WorkspaceSelectView.as_view(), name='workspace_select'),
    path('espacos/<int:pk>/convidar/', views.InviteMemberView.as_view(), name='invite_member'),
    path('convites/aceitar/<uuid:token>/', views.AcceptInvitationView.as_view(), name='accept_invitation'),
]
