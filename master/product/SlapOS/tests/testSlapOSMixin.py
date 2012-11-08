# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Vifib SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
##############################################################################

import random
import transaction
import unittest
import Products.Vifib.tests.VifibMixin
from Products.ERP5Type.tests.utils import DummyMailHost

class testSlapOSMixin(Products.Vifib.tests.VifibMixin.testVifibMixin):
  def _setUpDummyMailHost(self):
    """Do not play with NON persistent replacement of MailHost"""
    if not self.isLiveTest():
      super(testSlapOSMixin, self)._setUpDummyMailHost()

  def _restoreMailHost(self):
    """Do not play with NON persistent replacement of MailHost"""
    if not self.isLiveTest():
      super(testSlapOSMixin, self)._restoreMailHost()

  def beforeTearDown(self):
    if self.isLiveTest():
      self.deSetUpPersistentDummyMailHost()
      return

  def afterSetUp(self):
    if self.isLiveTest():
      self.setUpPersistentDummyMailHost()
      return
    self.portal.portal_caches.erp5_site_global_id = '%s' % random.random()
    self.portal.portal_caches._p_changed = 1
    transaction.commit()
    self.portal.portal_caches.updateCache()
    if getattr(self.portal, 'set_up_once_called', 0):
      return
    else:
      self.portal.set_up_once_called = 1
      self.bootstrapSite()
      self.portal._p_changed = 1
      transaction.commit()

  def deSetUpPersistentDummyMailHost(self):
    if 'MailHost' in self.portal.objectIds():
      self.portal.manage_delObjects(['MailHost'])
    self.portal.manage_addProduct['MailHost'].manage_addMailHost('MailHost')
    transaction.commit()

  def setUpPersistentDummyMailHost(self):
    if 'MailHost' in self.portal.objectIds():
      self.portal.manage_delObjects(['MailHost'])
    self.portal._setObject('MailHost', DummyMailHost('MailHost'))

    self.portal.email_from_address = 'romain@nexedi.com'
    self.portal.email_to_address = 'romain@nexedi.com'

  def bootstrapSite(self):
    self.setupPortalAlarms()
    self.setupPortalCertificateAuthority()
    self.setUpMemcached()

    self.clearCache()

    self.login()
    # Invoke Post-configurator script, this invokes all 
    # alarms related to configuration.
    self.portal.BusinessConfiguration_invokeSlapOSMasterPromiseAlarmList()
    transaction.commit()
    self.tic()
    self.logout()
    self.loginDefaultUser()

  def getBusinessTemplateList(self):
    """
    Install the business templates.
    """
    result = [
      'erp5_promise',
      'erp5_full_text_myisam_catalog',
      'erp5_core_proxy_field_legacy',
      'erp5_base',
      'erp5_workflow',
      'erp5_configurator',
      'slapos_configurator',
      'erp5_simulation',
      'erp5_pdm',
      'erp5_trade',
      'erp5_item',
      'erp5_forge',
      'erp5_ingestion_mysql_innodb_catalog',
      'erp5_ingestion',
      'erp5_crm',
      'erp5_jquery',
      'erp5_jquery_ui',
      'erp5_dhtml_style',
      'erp5_knowledge_pad',
      'erp5_web',
      'erp5_dms',
      'erp5_content_translation',
      'erp5_software_pdm',
      'erp5_computer_immobilisation',
      'erp5_accounting',
      'erp5_commerce',
      'erp5_xhtml_jquery_style',
      'erp5_credential',
      'erp5_km',
      'erp5_web_download_theme',
      'erp5_web_shacache',
      'erp5_data_set',
      'erp5_web_shadir',
      'slapos_cache',
      'slapos_cloud',
      'slapos_slap_tool',
      'slapos_category',
      'slapos_rest_api_tool_portal_type',
      'slapos_rest_api',
      'slapos_pdm',
      'slapos_web',
      'slapos_erp5',
    ]
    return result

  def _makeTree(self, requested_template_id='template_software_instance'):
    new_id = self.generateNewId()

    self.request_kw = dict(
        software_release=self.generateNewSoftwareReleaseUrl(),
        software_title=self.generateNewSoftwareTitle(),
        software_type=self.generateNewSoftwareType(),
        instance_xml=self.generateSafeXml(),
        sla_xml=self.generateEmptyXml(),
        shared=False,
        state="started"
    )

    # Clone person document
    self.person_user = self.portal.person_module.template_member.\
                                 Base_createCloneDocument(batch_mode=1)
    self.person_user.edit(
      title="live_test_%s" % new_id,
      reference="live_test_%s" % new_id,
      default_email_text="live_test_%s@example.org" % new_id,
    )

    self.person_user.validate()
    for assignment in self.person_user.contentValues(portal_type="Assignment"):
      assignment.open()
    transaction.commit()
    # prepare part of tree
    self.hosting_subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    self.software_instance = self.portal.software_instance_module\
        [requested_template_id].Base_createCloneDocument(batch_mode=1)

    self.hosting_subscription.edit(
        title=self.request_kw['software_title'],
        reference="TESTHS-%s" % new_id,
        url_string=self.request_kw['software_release'],
        source_reference=self.request_kw['software_type'],
        text_content=self.request_kw['instance_xml'],
        sla_xml=self.request_kw['sla_xml'],
        root_slave=self.request_kw['shared'],
        predecessor=self.software_instance.getRelativeUrl(),
        destination_section=self.person_user.getRelativeUrl()
    )
    self.hosting_subscription.validate()
    self.portal.portal_workflow._jumpToStateFor(self.hosting_subscription, 'start_requested')

    self.requested_software_instance = self.portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)
    self.software_instance.edit(
        title=self.request_kw['software_title'],
        reference="TESTSI-%s" % new_id,
        url_string=self.request_kw['software_release'],
        source_reference=self.request_kw['software_type'],
        text_content=self.request_kw['instance_xml'],
        sla_xml=self.request_kw['sla_xml'],
        specialise=self.hosting_subscription.getRelativeUrl(),
        predecessor=self.requested_software_instance.getRelativeUrl()
    )
    self.portal.portal_workflow._jumpToStateFor(self.software_instance, 'start_requested')
    self.software_instance.validate()

    self.requested_software_instance.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId(),
        url_string=self.request_kw['software_release'],
        source_reference=self.request_kw['software_type'],
        text_content=self.request_kw['instance_xml'],
        sla_xml=self.request_kw['sla_xml'],
        specialise=self.hosting_subscription.getRelativeUrl(),
    )
    self.portal.portal_workflow._jumpToStateFor(self.requested_software_instance, 'start_requested')
    self.requested_software_instance.validate()
    self.tic()

  def _makeComputer(self):
    self.computer = self.portal.computer_module.template_computer\
        .Base_createCloneDocument(batch_mode=1)
    reference = 'TESTCOMP-%s' % self.generateNewId()
    self.computer.edit(
        allocation_scope='open/public',
        capacity_scope='open',
        reference=reference,
        title=reference
        )
    self.computer.validate()
    reference = 'TESTPART-%s' % self.generateNewId()
    self.partition = self.computer.newContent(portal_type='Computer Partition',
      reference=reference,
      title=reference
    )
    self.partition.markFree()
    self.partition.validate()
    self.tic()

  def _makeComplexComputer(self):
    for i in range(1, 5):
      id_ = 'partition%s' % i
      p = self.computer.newContent(portal_type='Computer Partition',
        id=id_,
        title=id_,
        reference=id_,
        default_network_address_ip_address='ip_address_%s' % i,
        default_network_address_netmask='netmask_%s' % i)
      p.markFree()
      p.validate()

    self.start_requested_software_installation = self.portal.software_installation_module\
        .template_software_installation.Base_createCloneDocument(batch_mode=1)
    self.start_requested_software_installation.edit(
        url_string=self.generateNewSoftwareReleaseUrl(),
        aggregate=self.computer.getRelativeUrl(),
        reference='TESTSOFTINST-%s' % self.generateNewId(),
        title='Start requested for %s' % self.computer.getTitle()
    )
    self.start_requested_software_installation.validate()
    self.start_requested_software_installation.requestStart()

    self.destroy_requested_software_installation = self.portal.software_installation_module\
        .template_software_installation.Base_createCloneDocument(batch_mode=1)
    self.destroy_requested_software_installation.edit(
        url_string=self.generateNewSoftwareReleaseUrl(),
        aggregate=self.computer.getRelativeUrl(),
        reference='TESTSOFTINST-%s' % self.generateNewId(),
        title='Destroy requested for %s' % self.computer.getTitle()
    )
    self.destroy_requested_software_installation.validate()
    self.destroy_requested_software_installation.requestStart()
    self.destroy_requested_software_installation.requestDestroy()

    self.destroyed_software_installation = self.portal.software_installation_module\
        .template_software_installation.Base_createCloneDocument(batch_mode=1)
    self.destroyed_software_installation.edit(
        url_string=self.generateNewSoftwareReleaseUrl(),
        aggregate=self.computer.getRelativeUrl(),
        reference='TESTSOFTINST-%s' % self.generateNewId(),
        title='Destroyed for %s' % self.computer.getTitle()
    )
    self.destroyed_software_installation.validate()
    self.destroyed_software_installation.requestStart()
    self.destroyed_software_installation.requestDestroy()
    self.destroyed_software_installation.invalidate()

    self.computer.partition1.markBusy()
    self.computer.partition2.markBusy()
    self.computer.partition3.markBusy()

    # prepare some trees
    hosting_subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    hosting_subscription.edit(
    )
    hosting_subscription.validate()
    hosting_subscription.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId(),
    )
    kw = dict(
      software_release=\
          self.start_requested_software_installation.getUrlString(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=hosting_subscription.getTitle(),
      state='started'
    )
    hosting_subscription.requestStart(**kw)
    hosting_subscription.requestInstance(**kw)

    self.start_requested_software_instance = hosting_subscription.getPredecessorValue()
    self.start_requested_software_instance.edit(aggregate=self.computer.partition1.getRelativeUrl())

    hosting_subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    hosting_subscription.edit(
    )
    hosting_subscription.validate()
    hosting_subscription.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId(),
    )
    kw = dict(
      software_release=\
          self.start_requested_software_installation.getUrlString(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=hosting_subscription.getTitle(),
      state='stopped'
    )
    hosting_subscription.requestStop(**kw)
    hosting_subscription.requestInstance(**kw)

    self.stop_requested_software_instance = hosting_subscription.getPredecessorValue()
    self.stop_requested_software_instance.edit(
        aggregate=self.computer.partition2.getRelativeUrl()
    )

    hosting_subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    hosting_subscription.edit(
    )
    hosting_subscription.validate()
    hosting_subscription.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId(),
    )
    kw = dict(
      software_release=\
          self.start_requested_software_installation.getUrlString(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=hosting_subscription.getTitle(),
      state='stopped'
    )
    hosting_subscription.requestStop(**kw)
    hosting_subscription.requestInstance(**kw)

    kw['state'] = 'destroyed'
    hosting_subscription.requestDestroy(**kw)

    self.destroy_requested_software_instance = hosting_subscription.getPredecessorValue()
    self.destroy_requested_software_instance.requestDestroy(**kw)
    self.destroy_requested_software_instance.edit(
        aggregate=self.computer.partition3.getRelativeUrl()
    )

    hosting_subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    hosting_subscription.edit(
    )
    hosting_subscription.validate()
    hosting_subscription.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId(),
    )
    kw = dict(
      software_release=\
          self.start_requested_software_installation.getUrlString(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=hosting_subscription.getTitle(),
      state='stopped'
    )
    hosting_subscription.requestStop(**kw)
    hosting_subscription.requestInstance(**kw)

    kw['state'] = 'destroyed'
    hosting_subscription.requestDestroy(**kw)

    self.destroyed_software_instance = hosting_subscription.getPredecessorValue()
    self.destroyed_software_instance.edit(
        aggregate=self.computer.partition4.getRelativeUrl()
    )
    self.destroyed_software_instance.requestDestroy(**kw)
    self.destroyed_software_instance.invalidate()

    self.tic()
    self._cleaupREQUEST()

  def _cleaupREQUEST(self):
    self.portal.REQUEST['request_instance'] = None
    self.portal.REQUEST.headers = {}

  def generateNewId(self):
    return self.portal.portal_ids.generateNewId(
        id_group=('slapos_core_test'))

  def generateNewSoftwareReleaseUrl(self):
    return 'http://example.org/test%s.cfg' % self.generateNewId()

  def generateNewSoftwareType(self):
    return 'Type%s' % self.generateNewId()

  def generateNewSoftwareTitle(self):
    return 'Title%s' % self.generateNewId()

  def generateSafeXml(self):
    return '<?xml version="1.0" encoding="utf-8"?><instance><parameter '\
      'id="param">%s</parameter></instance>' % self.generateNewId()

  def generateEmptyXml(self):
    return '<?xml version="1.0" encoding="utf-8"?><instance></instance>'

class TestSlapOSDummy(testSlapOSMixin):
  run_all_test = 1
  def test(self):
    """Dummy test in order to fire up Business Template testing"""
    self.assertTrue(True)

  def getTitle(self):
    return "Dummy tests in order to have tests from BT5 run"

def test_suite():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(TestSlapOSDummy))
  return suite
