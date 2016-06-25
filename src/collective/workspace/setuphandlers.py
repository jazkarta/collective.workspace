from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.Extensions.Install import activatePluginInterfaces
from zope.component.hooks import getSite
from .interfaces import IHasWorkspace
from .interfaces import IWorkspace
from .pas import get_workspace_groups_plugin
import logging

logger = logging.getLogger('collective.workspace')


def setup_pas(context):
    if context.readDataFile('collective.workspace.txt') is None:
        return

    site = getSite()
    if 'workspace_groups' not in site.acl_users:
        site.acl_users.manage_addProduct[
            'collective.workspace'].addWorkspaceGroupManager(
            'workspace_groups', 'collective.workspace Groups',
            )
        activatePluginInterfaces(site, 'workspace_groups')


def migrate_groups(context):
    site = getSite()

    workspace_groups = get_workspace_groups_plugin(site)
    if hasattr(workspace_groups, '_groups'):
        # Already migrated
        return

    # Reinitialize groups plugin because its base class changed
    workspace_groups.__init__(workspace_groups.id, workspace_groups.title)

    # Store existing workspace group membership in workspace_groups
    catalog = getToolByName(site, 'portal_catalog')
    for b in catalog.unrestrictedSearchResults(
            object_provides=IHasWorkspace.__identifier__):
        logger.info('Migrating workspace groups for {}'.format(b.getPath()))
        workspace = IWorkspace(b._unrestrictedGetObject())
        for group_name in set(workspace.available_groups):
            group_id = '{}:{}'.format(group_name.encode('utf8'), b.UID)
            workspace_groups.addGroup(
                group_id,
                title='{}: {}'.format(group_name.encode('utf8'), b.Title),
            )
        for m in workspace:
            groups = m.groups
            new_groups = groups & set(workspace.available_groups)
            m._update_groups(set(), new_groups)
