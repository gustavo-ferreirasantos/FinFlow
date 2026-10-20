from .models import WorkspaceMember
from .utils import get_active_workspace


def active_workspace_processor(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'profile'):
        return {
            'active_workspace': None,
            'user_workspaces': [],
        }

    active_ws = get_active_workspace(request)

    memberships = WorkspaceMember.objects.filter(
        profile=request.user.profile
    ).select_related('workspace')

    user_workspaces = [member.workspace for member in memberships]

    return {
        'active_workspace': active_ws,
        'user_workspaces': user_workspaces,
    }
