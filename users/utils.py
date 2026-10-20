from .models import Workspace, WorkspaceMember


def get_active_workspace(request):
    if not request.user.is_authenticated:
        return None
    
    profile = getattr(request.user, 'profile', None)
    if not profile:
        return None
    
    workspace_id = request.session.get('active_workspace_id')

    if workspace_id:
        workspace = Workspace.objects.filter(
            id=workspace_id,
            members__profile=profile
        ).first()

        if workspace:
            return workspace

    first_membership = WorkspaceMember.objects.filter(
        profile=profile
    ).select_related('workspace').first()

    if first_membership:
        workspace = first_membership.workspace
        request.session['active_workspace_id'] = str(workspace.id)
        return workspace

    return None
