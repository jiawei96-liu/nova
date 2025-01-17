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

from nova.api.openstack.compute import instance_usage_audit_log as iual
from nova.policies import base as base_policy
from nova.policies import instance_usage_audit_log as iual_policies
from nova.tests.unit.api.openstack import fakes
from nova.tests.unit.policies import base


class InstanceUsageAuditLogPolicyTest(base.BasePolicyTest):
    """Test os-instance-usage-audit-log APIs policies with all possible
    context.
    This class defines the set of context with different roles
    which are allowed and not allowed to pass the policy checks.
    With those set of context, it will call the API operation and
    verify the expected behaviour.
    """

    def setUp(self):
        super(InstanceUsageAuditLogPolicyTest, self).setUp()
        self.controller = iual.InstanceUsageAuditLogController()
        self.req = fakes.HTTPRequest.blank('')
        self.controller.host_api.task_log_get_all = mock.MagicMock()
        self.controller.host_api.service_get_all = mock.MagicMock()

        # With legacy rule, all admin_api will be able to get instance usage
        # audit log.
        self.admin_authorized_contexts = [
            self.legacy_admin_context, self.system_admin_context,
            self.project_admin_context]

    def test_show_policy(self):
        rule_name = iual_policies.BASE_POLICY_NAME % 'show'
        self.common_policy_auth(self.admin_authorized_contexts,
                                rule_name, self.controller.show,
                                self.req, '2020-03-25 14:40:00')

    def test_index_policy(self):
        rule_name = iual_policies.BASE_POLICY_NAME % 'list'
        self.common_policy_auth(self.admin_authorized_contexts,
                                rule_name, self.controller.index,
                                self.req)


class InstanceUsageNoLegacyNoScopeTest(InstanceUsageAuditLogPolicyTest):
    """Test Instance Usage API policies with deprecated rules
    disabled, but scope checking still disabled.
    """

    without_deprecated_rules = True
    rules_without_deprecation = {
        iual_policies.BASE_POLICY_NAME % 'list':
            base_policy.ADMIN,
        iual_policies.BASE_POLICY_NAME % 'show':
            base_policy.ADMIN,
    }


class InstanceUsageScopeTypePolicyTest(InstanceUsageAuditLogPolicyTest):
    """Test os-instance-usage-audit-log APIs policies with system scope
    enabled.
    This class set the nova.conf [oslo_policy] enforce_scope to True
    so that we can switch on the scope checking on oslo policy side.
    It defines the set of context with scoped token
    which are allowed and not allowed to pass the policy checks.
    With those set of context, it will run the API operation and
    verify the expected behaviour.
    """

    def setUp(self):
        super(InstanceUsageScopeTypePolicyTest, self).setUp()
        self.flags(enforce_scope=True, group="oslo_policy")

        # Scope checks remove project users power.
        self.admin_authorized_contexts = [
            self.system_admin_context]


class InstanceUsageScopeTypeNoLegacyPolicyTest(
        InstanceUsageScopeTypePolicyTest):
    """Test Instance Usage Audit Log APIs policies with system scope enabled,
    and no more deprecated rules.
    """
    without_deprecated_rules = True
    rules_without_deprecation = {
        iual_policies.BASE_POLICY_NAME % 'list':
            base_policy.ADMIN,
        iual_policies.BASE_POLICY_NAME % 'show':
            base_policy.ADMIN,
    }
