#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from unittest import mock

import fixtures
from oslo_utils.fixture import uuidsentinel as uuids
from oslo_utils import timeutils

from nova.api.openstack.compute import server_diagnostics
from nova.compute import vm_states
from nova.policies import base as base_policy
from nova.policies import server_diagnostics as policies
from nova.tests.unit.api.openstack import fakes
from nova.tests.unit import fake_instance
from nova.tests.unit.policies import base


class ServerDiagnosticsPolicyTest(base.BasePolicyTest):
    """Test Server Diagnostics APIs policies with all possible context.

    This class defines the set of context with different roles
    which are allowed and not allowed to pass the policy checks.
    With those set of context, it will call the API operation and
    verify the expected behaviour.
    """

    def setUp(self):
        super(ServerDiagnosticsPolicyTest, self).setUp()
        self.controller = server_diagnostics.ServerDiagnosticsController()
        self.req = fakes.HTTPRequest.blank('', version='2.48')
        self.controller.compute_api.get_instance_diagnostics = mock.MagicMock()
        self.mock_get = self.useFixture(
            fixtures.MockPatch('nova.api.openstack.common.get_instance')).mock
        self.instance = fake_instance.fake_instance_obj(
                self.project_member_context, project_id=self.project_id,
                id=1, uuid=uuids.fake_id, vm_state=vm_states.ACTIVE,
                task_state=None, launched_at=timeutils.utcnow())
        self.mock_get.return_value = self.instance

        # With legacy rule, any admin is able get server diagnostics.
        self.project_admin_authorized_contexts = [
            self.legacy_admin_context, self.system_admin_context,
            self.project_admin_context]

    def test_server_diagnostics_policy(self):
        rule_name = policies.BASE_POLICY_NAME
        self.common_policy_auth(self.project_admin_authorized_contexts,
                                rule_name, self.controller.index,
                                self.req, self.instance.uuid)


class ServerDiagnosticsNoLegacyNoScopeTest(ServerDiagnosticsPolicyTest):
    """Test Server Diagnostics API policies with deprecated rules
    disabled, but scope checking still disabled.
    """

    without_deprecated_rules = True

    def setUp(self):
        super(ServerDiagnosticsNoLegacyNoScopeTest, self).setUp()
        self.project_admin_authorized_contexts = [
            self.project_admin_context]


class ServerDiagnosticsScopeTypePolicyTest(ServerDiagnosticsPolicyTest):
    """Test Server Diagnostics APIs policies with system scope enabled.

    This class set the nova.conf [oslo_policy] enforce_scope to True
    so that we can switch on the scope checking on oslo policy side.
    It defines the set of context with scoped token
    which are allowed and not allowed to pass the policy checks.
    With those set of context, it will run the API operation and
    verify the expected behaviour.
    """

    def setUp(self):
        super(ServerDiagnosticsScopeTypePolicyTest, self).setUp()
        self.flags(enforce_scope=True, group="oslo_policy")
        # With scope enabled, system admin is not allowed.
        self.project_admin_authorized_contexts = [
            self.legacy_admin_context, self.project_admin_context]


class ServerDiagnosticsScopeTypeNoLegacyPolicyTest(
    ServerDiagnosticsScopeTypePolicyTest):
    """Test Server Diagnostics APIs policies with system scope enabled,
    and no more deprecated rules.
    """
    without_deprecated_rules = True

    def setUp(self):
        super(ServerDiagnosticsScopeTypeNoLegacyPolicyTest, self).setUp()
        # with no legacy rule and scope enable., only project admin is able to
        # get server diagnostics.
        self.project_admin_authorized_contexts = [self.project_admin_context]


class ServerDiagnosticsOverridePolicyTest(
    ServerDiagnosticsScopeTypeNoLegacyPolicyTest):
    """Test Server Diagnostics APIs policies with system and project scoped
    but default to system roles only are allowed for project roles
    if override by operators. This test is with system scope enable
    and no more deprecated rules.
    """

    def setUp(self):
        super(ServerDiagnosticsOverridePolicyTest, self).setUp()
        rule = policies.BASE_POLICY_NAME
        # NOTE(gmann): override the rule to project member and verify it
        # work as policy is project scoped.
        self.policy.set_rules({
            rule: base_policy.PROJECT_MEMBER},
            overwrite=False)

        # Check that project member role as override above
        # is able to get server diagnostics.
        self.project_admin_authorized_contexts = [
            self.project_admin_context, self.project_member_context]
