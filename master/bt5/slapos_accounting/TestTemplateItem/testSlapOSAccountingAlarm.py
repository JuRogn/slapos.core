# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

import transaction
import functools
from Products.ERP5Type.tests.utils import createZODBPythonScript
from Products.SlapOS.tests.testSlapOSMixin import \
  testSlapOSMixin
import os
import tempfile
from DateTime import DateTime
from Products.ERP5Type.DateUtils import addToDate

def simulateInstance_solveInvoicingGeneration(func):
  @functools.wraps(func)
  def wrapped(self, *args, **kwargs):
    script_name = 'Instance_solveInvoicingGeneration'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by Instance_solveInvoicingGeneration') """ )
    transaction.commit()
    try:
      func(self, *args, **kwargs)
    finally:
      if script_name in self.portal.portal_skins.custom.objectIds():
        self.portal.portal_skins.custom.manage_delObjects(script_name)
      transaction.commit()
  return wrapped

class TestInstanceInvoicingAlarm(testSlapOSMixin):
  def afterSetUp(self):
    super(TestInstanceInvoicingAlarm, self).afterSetUp()

    self.software_instance_request_kw = dict(
      software_release=self.generateNewSoftwareReleaseUrl(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
    )

    self.slave_instance_request_kw = dict(
      software_release=self.generateNewSoftwareReleaseUrl(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=True,
    )

  def beforeTearDown(self):
    transaction.abort()

  def test_noSaleOrderPackingList_newSoftwareInstance(self):
    """
    Be sure no delivery is created synchronously (break old code behaviour)
    """
    instance = self.portal.software_instance_module.template_software_instance\
        .Base_createCloneDocument(batch_mode=1)
    instance.edit(title="TESTSI-%s" % self.generateNewId())
    instance.requestStart(**self.software_instance_request_kw)

    self.assertEqual(None, instance.getCausalityValue())

  def test_noSaleOrderPackingList_newSlaveInstance(self):
    """
    Be sure no delivery is created synchronously (break old code behaviour)
    """
    instance = self.portal.software_instance_module.template_slave_instance\
        .Base_createCloneDocument(batch_mode=1)
    instance.edit(title="TESTSI-%s" % self.generateNewId())
    instance.requestStart(**self.slave_instance_request_kw)
    self.tic()

    self.assertEqual(None, instance.getCausalityValue())

  @simulateInstance_solveInvoicingGeneration
  def test_alarm_findSoftwareInstance(self):
    new_id = self.generateNewId()
    instance = self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      title="Instance %s" % new_id,
      reference="TESTINST-%s" % new_id,
      destination_reference="TESTINST-%s" % new_id,
      ssl_certificate="foo",
      ssl_key="bar",
      )

    self.tic()

    self.portal.portal_alarms\
        .slapos_instance_invoicing\
        .activeSense()
    self.tic()
    self.assertEqual(
        'Visited by Instance_solveInvoicingGeneration',
        instance.workflow_history['edit_workflow'][-1]['comment'])

  @simulateInstance_solveInvoicingGeneration
  def test_alarm_findSlaveInstance(self):
    new_id = self.generateNewId()
    instance = self.portal.software_instance_module.newContent(
      portal_type='Slave Instance',
      title="Instance %s" % new_id,
      reference="TESTINST-%s" % new_id,
      destination_reference="TESTINST-%s" % new_id,
      )

    self.tic()

    self.portal.portal_alarms\
        .slapos_instance_invoicing\
        .activeSense()
    self.tic()
    self.assertEqual(
        'Visited by Instance_solveInvoicingGeneration',
        instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_solved_instance(self):
    instance = self.portal.software_instance_module\
        .template_slave_instance.Base_createCloneDocument(batch_mode=1)
    new_id = self.generateNewId()
    instance.edit(
      title="Instance %s" % new_id,
      reference="TESTINST-%s" % new_id,
      destination_reference="TESTINST-%s" % new_id,
    )

    request_time = DateTime('2012/01/01')
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Simulated request instance',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'destroyed',
        'time': request_time,
        'action': 'request_instance'
    })
    self.portal.portal_workflow._jumpToStateFor(instance, 'solved')

    instance.Instance_solveInvoicingGeneration()
    self.assertEqual(instance.getCausalityState(), 'solved')
    self.assertEqual(None, instance.getCausalityValue())

  def test_instance_in_draft_state(self):
    instance = self.portal.software_instance_module\
        .template_slave_instance.Base_createCloneDocument(batch_mode=1)
    new_id = self.generateNewId()
    instance.edit(
      title="Instance %s" % new_id,
      reference="TESTINST-%s" % new_id,
      destination_reference="TESTINST-%s" % new_id,
    )
    self.portal.portal_workflow._jumpToStateFor(instance, 'diverged')
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Stay in draft',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'draft',
        'time': DateTime(),
        'action': 'foo_transition'
    })

    instance.Instance_solveInvoicingGeneration()
    self.assertEqual(instance.getCausalityState(), 'solved')
    self.assertEqual(None, instance.getCausalityValue())

  def test_instance_in_unknown_state(self):
    instance = self.portal.software_instance_module\
        .template_slave_instance.Base_createCloneDocument(batch_mode=1)
    new_id = self.generateNewId()
    instance.edit(
      title="Instance %s" % new_id,
      reference="TESTINST-%s" % new_id,
      destination_reference="TESTINST-%s" % new_id,
    )
    self.portal.portal_workflow._jumpToStateFor(instance, 'diverged')
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Stay in unknown state',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'unknown_state',
        'time': DateTime(),
        'action': 'foo_transition'
    })

    self.assertRaises(AssertionError, instance.Instance_solveInvoicingGeneration) 

  def test_instance_in_early_destroyed_state(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription.edit(
      reference='TESTHS-%s' % self.generateNewId(),
      destination_section_value=person)
    instance = self.portal.software_instance_module\
        .template_slave_instance.Base_createCloneDocument(batch_mode=1)
    new_id = self.generateNewId()
    instance.edit(
      title="Instance %s" % new_id,
      reference="TESTINST-%s" % new_id,
      destination_reference="TESTINST-%s" % new_id,
      specialise_value=subscription,
    )
    self.portal.portal_workflow._jumpToStateFor(instance, 'diverged')
    start_date = instance.workflow_history\
      ['instance_slap_interface_workflow'][0]['time']
    stop_date = DateTime('2222/11/15')
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Directly in destroyed state',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'destroy_requested',
        'time': stop_date,
        'action': 'foo_transition'
    })

    instance.Instance_solveInvoicingGeneration()
    self.assertEqual(instance.getCausalityState(), 'solved')
    self.assertNotEqual(None, instance.getCausalityValue())
    self.assertEqual(2, instance.getInvoicingSynchronizationPointer())
    delivery = instance.getCausalityValue()

    setup_line, update_line, destroy_line =\
      self.check_instance_delivery(delivery, start_date, stop_date, person, 2)
    self.check_instance_movement(setup_line, instance, subscription, 1)
    self.check_instance_movement(destroy_line, instance, subscription, 1)

  def check_instance_delivery(self, delivery, start_date, stop_date, 
                              person, line_count):
    packing_list_line = delivery.contentValues(
      portal_type='Sale Packing List Line')
    self.assertEqual(len(packing_list_line), line_count)
    self.assertEqual(delivery.getDestinationValue(), person)
    self.assertEqual(delivery.getDestinationSectionValue(), person)
    self.assertEqual(delivery.getDestinationDecisionValue(), person)
    self.assertEqual(delivery.getStopDate(), stop_date)
    self.assertEqual(delivery.getStartDate(), start_date)
    self.assertEqual(delivery.getSimulationState(), 'delivered')
    self.assertEqual(delivery.getCausalityState(), 'building')

    # Hardcoded, but, no idea how to not make it...
    setup_line = ([None]+[x for x in packing_list_line \
      if x.getResource() == 'service_module/slapos_instance_setup'])[-1]
    destroy_line = ([None]+[x for x in packing_list_line \
      if x.getResource() == 'service_module/slapos_instance_cleanup'])[-1]
    update_line = ([None]+[x for x in packing_list_line \
      if x.getResource() == 'service_module/slapos_instance_update'])[-1]
    return setup_line, update_line, destroy_line

  def check_instance_movement(self, movement, instance, 
                              subscription, quantity):
    self.assertEqual(movement.getQuantity(), quantity)
    self.assertSameSet(movement.getAggregateValueList(),
                       [instance, subscription])
    self.assertEqual(len(movement.contentValues()), 0)

  def test_instance_create_non_destroyed_state(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription.edit(
      reference='TESTHS-%s' % self.generateNewId(),
      destination_section_value=person)
    instance = self.portal.software_instance_module\
        .template_slave_instance.Base_createCloneDocument(batch_mode=1)
    new_id = self.generateNewId()
    instance.edit(
      title="Instance %s" % new_id,
      reference="TESTINST-%s" % new_id,
      destination_reference="TESTINST-%s" % new_id,
      specialise_value=subscription,
    )
    self.portal.portal_workflow._jumpToStateFor(instance, 'diverged')
    start_date = instance.workflow_history\
      ['instance_slap_interface_workflow'][0]['time']
    stop_date = DateTime('2222/11/15')
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Directly in start state',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'start_requested',
        'time': stop_date,
        'action': 'foo_transition'
    })

    instance.Instance_solveInvoicingGeneration()
    self.assertEqual(instance.getCausalityState(), 'solved')
    self.assertNotEqual(None, instance.getCausalityValue())
    self.assertEqual(2, instance.getInvoicingSynchronizationPointer())
    delivery = instance.getCausalityValue()

    setup_line, update_line, destroy_line =\
      self.check_instance_delivery(delivery, start_date, stop_date, person, 1)
    self.check_instance_movement(setup_line, instance, subscription, 1)

  def test_instance_create_non_destroyed_with_update_state(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription.edit(
      reference='TESTHS-%s' % self.generateNewId(),
      destination_section_value=person)
    instance = self.portal.software_instance_module\
        .template_slave_instance.Base_createCloneDocument(batch_mode=1)
    new_id = self.generateNewId()
    instance.edit(
      title="Instance %s" % new_id,
      reference="TESTINST-%s" % new_id,
      destination_reference="TESTINST-%s" % new_id,
      specialise_value=subscription,
    )
    self.portal.portal_workflow._jumpToStateFor(instance, 'diverged')
    start_date = instance.workflow_history\
      ['instance_slap_interface_workflow'][0]['time']
    stop_date = DateTime('2222/11/15')
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Update',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'foo_state',
        'time': stop_date-1,
        'action': 'foo_transition'
    })
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Update',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'foo_state',
        'time': stop_date-2,
        'action': 'foo_transition'
    })
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Directly in start state',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'start_requested',
        'time': stop_date,
        'action': 'foo_transition'
    })

    instance.Instance_solveInvoicingGeneration()
    self.assertEqual(instance.getCausalityState(), 'solved')
    self.assertNotEqual(None, instance.getCausalityValue())
    self.assertEqual(4, instance.getInvoicingSynchronizationPointer())
    delivery = instance.getCausalityValue()

    setup_line, update_line, destroy_line =\
      self.check_instance_delivery(delivery, start_date, stop_date, person, 2)
    self.check_instance_movement(setup_line, instance, subscription, 1)
    self.check_instance_movement(update_line, instance, subscription, 2)

  def test_instance_create_destroyed_with_update_state(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription.edit(
      reference='TESTHS-%s' % self.generateNewId(),
      destination_section_value=person)
    instance = self.portal.software_instance_module\
        .template_slave_instance.Base_createCloneDocument(batch_mode=1)
    new_id = self.generateNewId()
    instance.edit(
      title="Instance %s" % new_id,
      reference="TESTINST-%s" % new_id,
      destination_reference="TESTINST-%s" % new_id,
      specialise_value=subscription,
    )
    self.portal.portal_workflow._jumpToStateFor(instance, 'diverged')
    start_date = instance.workflow_history\
      ['instance_slap_interface_workflow'][0]['time']
    stop_date = DateTime('2222/11/15')
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Update',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'foo_state',
        'time': stop_date-1,
        'action': 'foo_transition'
    })
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Update',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'foo_state',
        'time': stop_date-2,
        'action': 'foo_transition'
    })
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Directly in destroy state',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'destroy_requested',
        'time': stop_date,
        'action': 'foo_transition'
    })

    instance.Instance_solveInvoicingGeneration()
    self.assertEqual(instance.getCausalityState(), 'solved')
    self.assertNotEqual(None, instance.getCausalityValue())
    self.assertEqual(4, instance.getInvoicingSynchronizationPointer())
    delivery = instance.getCausalityValue()

    setup_line, update_line, destroy_line =\
      self.check_instance_delivery(delivery, start_date, stop_date, person, 3)
    self.check_instance_movement(setup_line, instance, subscription, 1)
    self.check_instance_movement(update_line, instance, subscription, 1)
    self.check_instance_movement(destroy_line, instance, subscription, 1)

  def test_instance_update_non_destroyed_state(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription.edit(
      reference='TESTHS-%s' % self.generateNewId(),
      destination_section_value=person)
    instance = self.portal.software_instance_module\
        .template_slave_instance.Base_createCloneDocument(batch_mode=1)
    previous_delivery = self.portal.sale_packing_list_module.newContent(
      portal_type='Sale Packing List')
    new_id = self.generateNewId()
    instance.edit(
      title="Instance %s" % new_id,
      reference="TESTINST-%s" % new_id,
      destination_reference="TESTINST-%s" % new_id,
      specialise_value=subscription,
      invoicing_synchronization_pointer=2,
      causality_value=previous_delivery,
    )
    self.portal.portal_workflow._jumpToStateFor(instance, 'diverged')
    stop_date = DateTime('2222/11/15')
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Update',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'foo_state',
        'time': stop_date-1,
        'action': 'foo_transition'
    })
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Update',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'foo_state',
        'time': stop_date-2,
        'action': 'foo_transition'
    })
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Directly in start state',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'start_requested',
        'time': stop_date,
        'action': 'foo_transition'
    })
    start_date = stop_date-1

    instance.Instance_solveInvoicingGeneration()
    self.assertEqual(instance.getCausalityState(), 'solved')
    self.assertNotEqual(None, instance.getCausalityValue())
    self.assertEqual(4, instance.getInvoicingSynchronizationPointer())
    delivery = instance.getCausalityValue()

    setup_line, update_line, destroy_line =\
      self.check_instance_delivery(delivery, start_date, stop_date, person, 1)
    self.check_instance_movement(update_line, instance, subscription, 2)

  def test_instance_update_destroyed_state(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription.edit(
      reference='TESTHS-%s' % self.generateNewId(),
      destination_section_value=person)
    instance = self.portal.software_instance_module\
        .template_slave_instance.Base_createCloneDocument(batch_mode=1)
    previous_delivery = self.portal.sale_packing_list_module.newContent(
      portal_type='Sale Packing List')
    new_id = self.generateNewId()
    instance.edit(
      title="Instance %s" % new_id,
      reference="TESTINST-%s" % new_id,
      destination_reference="TESTINST-%s" % new_id,
      specialise_value=subscription,
      invoicing_synchronization_pointer=2,
      causality_value=previous_delivery,
    )
    self.portal.portal_workflow._jumpToStateFor(instance, 'diverged')
    stop_date = DateTime('2222/11/15')
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Update',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'foo_state',
        'time': stop_date-1,
        'action': 'foo_transition'
    })
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Update',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'foo_state',
        'time': stop_date-2,
        'action': 'foo_transition'
    })
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Directly in start state',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'destroy_requested',
        'time': stop_date,
        'action': 'foo_transition'
    })
    start_date = stop_date-1

    instance.Instance_solveInvoicingGeneration()
    self.assertEqual(instance.getCausalityState(), 'solved')
    self.assertNotEqual(None, instance.getCausalityValue())
    self.assertEqual(4, instance.getInvoicingSynchronizationPointer())
    delivery = instance.getCausalityValue()

    setup_line, update_line, destroy_line =\
      self.check_instance_delivery(delivery, start_date, stop_date, person, 2)
    self.check_instance_movement(update_line, instance, subscription, 1)
    self.check_instance_movement(destroy_line, instance, subscription, 1)

  def test_instance_update_already_destroyed(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription.edit(
      reference='TESTHS-%s' % self.generateNewId(),
      destination_section_value=person)
    instance = self.portal.software_instance_module\
        .template_slave_instance.Base_createCloneDocument(batch_mode=1)
    previous_delivery = self.portal.sale_packing_list_module.newContent(
      portal_type='Sale Packing List')
    new_id = self.generateNewId()
    instance.edit(
      title="Instance %s" % new_id,
      reference="TESTINST-%s" % new_id,
      destination_reference="TESTINST-%s" % new_id,
      specialise_value=subscription,
      invoicing_synchronization_pointer=2,
      causality_value=previous_delivery,
    )
    self.portal.portal_workflow._jumpToStateFor(instance, 'diverged')
    stop_date = DateTime('2222/11/15')
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Update',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'destroy_requested',
        'time': stop_date-1,
        'action': 'foo_transition'
    })
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Update',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'destroy_requested',
        'time': stop_date-2,
        'action': 'foo_transition'
    })
    instance.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Directly in start state',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'destroy_requested',
        'time': stop_date,
        'action': 'foo_transition'
    })
    start_date = stop_date-1

    instance.Instance_solveInvoicingGeneration()
    self.assertEqual(instance.getCausalityState(), 'solved')
    self.assertNotEqual(None, instance.getCausalityValue())
    self.assertEqual(4, instance.getInvoicingSynchronizationPointer())
    delivery = instance.getCausalityValue()

    setup_line, update_line, destroy_line =\
      self.check_instance_delivery(delivery, start_date, stop_date, person, 1)
    self.check_instance_movement(update_line, instance, subscription, 2)

def simulateHostingSubscription_requestUpdateOpenSaleOrder(func):
  @functools.wraps(func)
  def wrapped(self, *args, **kwargs):
    script_name = 'HostingSubscription_requestUpdateOpenSaleOrder'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by HostingSubscription_requestUpdateOpenSaleOrder') """ )
    transaction.commit()
    try:
      func(self, *args, **kwargs)
    finally:
      transaction.abort()
      if script_name in self.portal.portal_skins.custom.objectIds():
        self.portal.portal_skins.custom.manage_delObjects(script_name)
      transaction.commit()
  return wrapped

class TestOpenSaleOrderAlarm(testSlapOSMixin):
  def test_noOSO_newPerson(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    self.tic()

    self.assertEqual(None, self.portal.portal_catalog.getResultValue(
        portal_type='Open Sale Order',
        default_destination_section_uid=person.getUid()
    ))

  def test_noOSO_after_fixConsistency(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    self.tic()
    person.fixConsistency()
    self.tic()

    self.assertEqual(None, self.portal.portal_catalog.getResultValue(
        portal_type='Open Sale Order',
        default_destination_section_uid=person.getUid()
    ))

  def test_OSO_after_Person_updateOpenSaleOrder(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    self.tic()

    person.Person_updateOpenSaleOrder()
    self.tic()

    open_sale_order_list = self.portal.portal_catalog(
        validation_state='validated',
        portal_type='Open Sale Order',
        default_destination_section_uid=person.getUid()
    )
    self.assertEqual(1, len(open_sale_order_list))
    open_sale_order = open_sale_order_list[0]

    self.assertEqual('SlapOS Subscription Open Sale Order',
        open_sale_order.getTitle())
    self.assertEqual(0, len(open_sale_order.contentValues()))
    open_sale_order_template = self.portal.restrictedTraverse(
        self.portal.portal_preferences.getPreferredOpenSaleOrderTemplate())
    self.assertTrue(all([q in open_sale_order.getCategoryList() \
        for q in open_sale_order_template.getCategoryList()]))

  @simulateHostingSubscription_requestUpdateOpenSaleOrder
  def test_alarm_HS_validated(self):
    subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId())
    self.portal.portal_workflow._jumpToStateFor(subscription, 'validated')
    self.tic()

    self.portal.portal_alarms\
        .slapos_request_update_hosting_subscription_open_sale_order\
        .activeSense()
    self.tic()
    self.assertEqual(
        'Visited by HostingSubscription_requestUpdateOpenSaleOrder',
        subscription.workflow_history['edit_workflow'][-1]['comment'])

  @simulateHostingSubscription_requestUpdateOpenSaleOrder
  def test_alarm_HS_validated_OSO_invalidated(self):
    subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId())
    self.portal.portal_workflow._jumpToStateFor(subscription, 'validated')

    open_sale_order = self.portal.open_sale_order_module\
        .template_open_sale_order.Base_createCloneDocument(batch_mode=1)
    open_sale_order.edit(reference='TESTOSO-%s' % self.generateNewId())
    open_sale_order.newContent(portal_type='Open Sale Order Line',
        aggregate=subscription.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(open_sale_order, 'invalidated')
    self.tic()

    self.portal.portal_alarms\
        .slapos_request_update_hosting_subscription_open_sale_order\
        .activeSense()
    self.tic()
    self.assertEqual(
        'Visited by HostingSubscription_requestUpdateOpenSaleOrder',
        subscription.workflow_history['edit_workflow'][-1]['comment'])

  @simulateHostingSubscription_requestUpdateOpenSaleOrder
  def test_alarm_HS_archived(self):
    subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId())
    self.portal.portal_workflow._jumpToStateFor(subscription, 'archived')
    self.tic()

    self.portal.portal_alarms\
        .slapos_request_update_hosting_subscription_open_sale_order\
        .activeSense()
    self.tic()
    self.assertEqual(
        'Visited by HostingSubscription_requestUpdateOpenSaleOrder',
        subscription.workflow_history['edit_workflow'][-1]['comment'])

  @simulateHostingSubscription_requestUpdateOpenSaleOrder
  def test_alarm_HS_archived_OSO_validated(self):
    subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId())
    self.portal.portal_workflow._jumpToStateFor(subscription, 'archived')

    open_sale_order = self.portal.open_sale_order_module\
        .template_open_sale_order.Base_createCloneDocument(batch_mode=1)
    open_sale_order.edit(reference='TESTOSO-%s' % self.generateNewId())
    open_sale_order.newContent(portal_type='Open Sale Order Line',
        aggregate=subscription.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(open_sale_order, 'validated')
    self.tic()

    self.portal.portal_alarms\
        .slapos_request_update_hosting_subscription_open_sale_order\
        .activeSense()
    self.tic()
    self.assertEqual(
        'Visited by HostingSubscription_requestUpdateOpenSaleOrder',
        subscription.workflow_history['edit_workflow'][-1]['comment'])

  @simulateHostingSubscription_requestUpdateOpenSaleOrder
  def test_alarm_HS_validated_OSO_validated(self):
    subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId())
    self.portal.portal_workflow._jumpToStateFor(subscription, 'validated')

    open_sale_order = self.portal.open_sale_order_module\
        .template_open_sale_order.Base_createCloneDocument(batch_mode=1)
    open_sale_order.edit(reference='TESTOSO-%s' % self.generateNewId())
    open_sale_order.newContent(portal_type='Open Sale Order Line',
        aggregate=subscription.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(open_sale_order, 'validated')
    self.tic()

    self.portal.portal_alarms\
        .slapos_request_update_hosting_subscription_open_sale_order\
        .activeSense()
    self.tic()
    self.assertNotEqual(
        'Visited by HostingSubscription_requestUpdateOpenSaleOrder',
        subscription.workflow_history['edit_workflow'][-1]['comment'])

  @simulateHostingSubscription_requestUpdateOpenSaleOrder
  def test_alarm_HS_archived_OSO_invalidated(self):
    subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId())
    self.portal.portal_workflow._jumpToStateFor(subscription, 'archived')

    open_sale_order = self.portal.open_sale_order_module\
        .template_open_sale_order.Base_createCloneDocument(batch_mode=1)
    open_sale_order.edit(reference='TESTOSO-%s' % self.generateNewId())
    open_sale_order.newContent(portal_type='Open Sale Order Line',
        aggregate=subscription.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(open_sale_order, 'invalidated')
    self.tic()

    self.portal.portal_alarms\
        .slapos_request_update_hosting_subscription_open_sale_order\
        .activeSense()
    self.tic()
    self.assertNotEqual(
        'Visited by HostingSubscription_requestUpdateOpenSaleOrder',
        subscription.workflow_history['edit_workflow'][-1]['comment'])

class TestHostingSubscription_requestUpdateOpenSaleOrder(testSlapOSMixin):
  def test_empty_HostingSubscription(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    self.tic()
    subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId(),
        destination_section=person.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(subscription, 'validated')
    self.tic()

    subscription.HostingSubscription_requestUpdateOpenSaleOrder()
    self.tic()

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_section_uid=person.getUid()
    )

    self.assertEqual(1,len(open_sale_order_list))
    open_sale_order = open_sale_order_list[0].getObject()
    self.assertEqual('validated', open_sale_order.getValidationState())

    open_sale_order_line_list = open_sale_order.contentValues(
        portal_type='Open Sale Order Line')

    self.assertEqual(1, len(open_sale_order_line_list))
    line = open_sale_order_line_list[0].getObject()

    self.assertEqual(subscription.getRelativeUrl(), line.getAggregate())
    open_sale_order_line_template = self.portal.restrictedTraverse(
        self.portal.portal_preferences.getPreferredOpenSaleOrderLineTemplate())
    self.assertEqual(open_sale_order_line_template.getResource(),
        line.getResource())
    self.assertTrue(all([q in line.getCategoryList() \
        for q in open_sale_order_line_template.getCategoryList()]))
    self.assertEqual(open_sale_order_line_template.getQuantity(),
        line.getQuantity())
    self.assertEqual(open_sale_order_line_template.getPrice(),
        line.getPrice())
    self.assertEqual(None, line.getStartDate())

  def test_usualLifetime_HostingSubscription(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    self.tic()
    subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId(),
        title='Test Title %s' % self.generateNewId(),
        destination_section=person.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(subscription, 'validated')

    request_time = DateTime('2012/01/01')
    subscription.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Simulated request instance',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'start_requested',
        'time': request_time,
        'action': 'request_instance'
    })
    self.tic()

    subscription.HostingSubscription_requestUpdateOpenSaleOrder()
    self.tic()

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_section_uid=person.getUid()
    )

    self.assertEqual(1, len(open_sale_order_list))
    open_sale_order = open_sale_order_list[0].getObject()
    self.assertEqual('validated', open_sale_order.getValidationState())

    open_sale_order_line_list = open_sale_order.contentValues(
        portal_type='Open Sale Order Line')

    self.assertEqual(1, len(open_sale_order_line_list))
    line = open_sale_order_line_list[0].getObject()

    # calculate stop date to be after now, begin with start date with precision
    # of month
    stop_date = request_time
    now = DateTime()
    while stop_date < now:
      stop_date = addToDate(stop_date, to_add={'month': 1})
    self.assertEqual(stop_date, line.getStopDate())

    self.assertEqual(subscription.getRelativeUrl(), line.getAggregate())
    open_sale_order_line_template = self.portal.restrictedTraverse(
        self.portal.portal_preferences.getPreferredOpenSaleOrderLineTemplate())
    self.assertTrue(all([q in line.getCategoryList() \
        for q in open_sale_order_line_template.getCategoryList()]))
    self.assertEqual(open_sale_order_line_template.getResource(),
        line.getResource())
    self.assertEqual(open_sale_order_line_template.getQuantity(),
        line.getQuantity())
    self.assertEqual(open_sale_order_line_template.getPrice(),
        line.getPrice())
    self.assertEqual(request_time, line.getStartDate())
    self.assertEqual(stop_date, line.getStopDate())

    destroy_time = DateTime('2012/02/01')
    subscription.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Simulated request instance',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'destroy_requested',
        'time': destroy_time,
        'action': 'request_destroy'
    })
    self.tic()

    subscription.HostingSubscription_requestUpdateOpenSaleOrder()
    self.tic()

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_section_uid=person.getUid()
    )

    self.assertEqual(2, len(open_sale_order_list))
    validated_open_sale_order_list = [q for q in open_sale_order_list
        if q.getValidationState() == 'validated']
    archived_open_sale_order_list = [q for q in open_sale_order_list
        if q.getValidationState() == 'archived']
    self.assertEqual(1, len(validated_open_sale_order_list))
    self.assertEqual(1, len(archived_open_sale_order_list))
    validated_open_sale_order = validated_open_sale_order_list[0].getObject()
    archived_open_sale_order = archived_open_sale_order_list[0]\
        .getObject()
    self.assertEqual(open_sale_order.getRelativeUrl(),
        archived_open_sale_order.getRelativeUrl())

    validated_line_list = validated_open_sale_order.contentValues(
        portal_type='Open Sale Order Line')
    archived_line_list = archived_open_sale_order.contentValues(
        portal_type='Open Sale Order Line')
    self.assertEqual(0, len(validated_line_list))
    self.assertEqual(1, len(archived_line_list))

    archived_line = archived_line_list[0].getObject()

    self.assertEqual(line.getRelativeUrl(), archived_line.getRelativeUrl())

    self.assertEqual(subscription.getRelativeUrl(),
        archived_line.getAggregate())
    self.assertTrue(all([q in archived_line.getCategoryList() \
        for q in open_sale_order_line_template.getCategoryList()]))
    self.assertEqual(open_sale_order_line_template.getResource(),
        archived_line.getResource())
    self.assertEqual(open_sale_order_line_template.getQuantity(),
        line.getQuantity())
    self.assertEqual(open_sale_order_line_template.getPrice(),
        line.getPrice())
    self.assertEqual(request_time, archived_line.getStartDate())
    self.assertEqual(stop_date, line.getStopDate())

  def test_lateAnalysed_HostingSubscription(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    self.tic()
    subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId(),
        title='Test Title %s' % self.generateNewId(),
        destination_section=person.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(subscription, 'validated')

    request_time = DateTime('2012/01/01')
    subscription.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Simulated request instance',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'start_requested',
        'time': request_time,
        'action': 'request_instance'
    })

    destroy_time = DateTime('2012/02/01')
    subscription.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Simulated request instance',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'destroy_requested',
        'time': destroy_time,
        'action': 'request_destroy'
    })
    self.tic()

    subscription.HostingSubscription_requestUpdateOpenSaleOrder()
    self.tic()

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_section_uid=person.getUid()
    )

    self.assertEqual(1, len(open_sale_order_list))
    open_sale_order = open_sale_order_list[0].getObject()
    self.assertEqual('validated', open_sale_order.getValidationState())

    open_sale_order_line_list = open_sale_order.contentValues(
        portal_type='Open Sale Order Line')

    self.assertEqual(1, len(open_sale_order_line_list))
    line = open_sale_order_line_list[0].getObject()

    self.assertEqual(subscription.getRelativeUrl(), line.getAggregate())
    open_sale_order_line_template = self.portal.restrictedTraverse(
        self.portal.portal_preferences.getPreferredOpenSaleOrderLineTemplate())
    self.assertTrue(all([q in line.getCategoryList() \
        for q in open_sale_order_line_template.getCategoryList()]))
    self.assertEqual(open_sale_order_line_template.getResource(),
        line.getResource())
    self.assertEqual(open_sale_order_line_template.getQuantity(),
        line.getQuantity())
    self.assertEqual(open_sale_order_line_template.getPrice(),
        line.getPrice())
    self.assertEqual(request_time, line.getStartDate())

    stop_date = request_time
    now = DateTime()
    while stop_date < now:
      stop_date = addToDate(stop_date, to_add={'month': 1})
    self.assertEqual(stop_date, line.getStopDate())

  def test_two_HostingSubscription(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    self.tic()
    subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId(),
        title='Test Title %s' % self.generateNewId(),
        destination_section=person.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(subscription, 'validated')

    request_time = DateTime('2012/01/01')
    subscription.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Simulated request instance',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'start_requested',
        'time': request_time,
        'action': 'request_instance'
    })
    self.tic()

    subscription.HostingSubscription_requestUpdateOpenSaleOrder()
    self.tic()

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_section_uid=person.getUid()
    )

    self.assertEqual(1, len(open_sale_order_list))
    open_sale_order = open_sale_order_list[0].getObject()
    self.assertEqual('validated', open_sale_order.getValidationState())

    open_sale_order_line_list = open_sale_order.contentValues(
        portal_type='Open Sale Order Line')

    self.assertEqual(1, len(open_sale_order_line_list))
    line = open_sale_order_line_list[0].getObject()

    self.assertEqual(subscription.getRelativeUrl(), line.getAggregate())
    open_sale_order_line_template = self.portal.restrictedTraverse(
        self.portal.portal_preferences.getPreferredOpenSaleOrderLineTemplate())
    self.assertTrue(all([q in line.getCategoryList() \
        for q in open_sale_order_line_template.getCategoryList()]))
    self.assertEqual(open_sale_order_line_template.getResource(),
        line.getResource())
    self.assertEqual(open_sale_order_line_template.getQuantity(),
        line.getQuantity())
    self.assertEqual(open_sale_order_line_template.getPrice(),
        line.getPrice())
    self.assertEqual(request_time, line.getStartDate())

    # calculate stop date to be after now, begin with start date with precision
    # of month
    stop_date = request_time
    now = DateTime()
    while stop_date < now:
      stop_date = addToDate(stop_date, to_add={'month': 1})
    self.assertEqual(stop_date, line.getStopDate())

    subscription2 = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    subscription2.edit(reference='TESTHS-%s' % self.generateNewId(),
        title='Test Title %s' % self.generateNewId(),
        destination_section=person.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(subscription2, 'validated')

    request_time_2 = DateTime('2012/08/01')
    subscription2.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Simulated request instance',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'start_requested',
        'time': request_time_2,
        'action': 'request_instance'
    })
    self.tic()

    subscription2.HostingSubscription_requestUpdateOpenSaleOrder()
    self.tic()

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_section_uid=person.getUid()
    )

    self.assertEqual(2, len(open_sale_order_list))
    validated_open_sale_order_list = [q for q in open_sale_order_list
        if q.getValidationState() == 'validated']
    archived_open_sale_order_list = [q for q in open_sale_order_list
        if q.getValidationState() == 'archived']
    self.assertEqual(1, len(validated_open_sale_order_list))
    self.assertEqual(1, len(archived_open_sale_order_list))
    validated_open_sale_order = validated_open_sale_order_list[0].getObject()
    archived_open_sale_order = archived_open_sale_order_list[0]\
        .getObject()
    self.assertEqual(open_sale_order.getRelativeUrl(),
        archived_open_sale_order.getRelativeUrl())

    validated_line_list = validated_open_sale_order.contentValues(
        portal_type='Open Sale Order Line')
    archived_line_list = archived_open_sale_order.contentValues(
        portal_type='Open Sale Order Line')
    self.assertEqual(2, len(validated_line_list))
    self.assertEqual(1, len(archived_line_list))

    archived_line = archived_line_list[0].getObject()

    self.assertEqual(line.getRelativeUrl(), archived_line.getRelativeUrl())

    self.assertEqual(subscription.getRelativeUrl(),
        archived_line.getAggregate())
    self.assertTrue(all([q in archived_line.getCategoryList() \
        for q in open_sale_order_line_template.getCategoryList()]))
    self.assertEqual(open_sale_order_line_template.getResource(),
        archived_line.getResource())
    self.assertEqual(open_sale_order_line_template.getQuantity(),
        line.getQuantity())
    self.assertEqual(open_sale_order_line_template.getPrice(),
        line.getPrice())
    self.assertEqual(request_time, archived_line.getStartDate())
    self.assertEqual(stop_date, archived_line.getStopDate())

    stop_date_2 = request_time_2
    now = DateTime()
    while stop_date_2 < now:
      stop_date_2 = addToDate(stop_date_2, to_add={'month': 1})

    validated_line_1 = [q for q in validated_line_list if q.getAggregate() == \
        subscription.getRelativeUrl()][0]
    validated_line_2 = [q for q in validated_line_list if q.getAggregate() == \
        subscription2.getRelativeUrl()][0]

    self.assertTrue(all([q in validated_line_1.getCategoryList() \
        for q in open_sale_order_line_template.getCategoryList()]))
    self.assertEqual(open_sale_order_line_template.getResource(),
        validated_line_1.getResource())
    self.assertEqual(open_sale_order_line_template.getQuantity(),
        line.getQuantity())
    self.assertEqual(open_sale_order_line_template.getPrice(),
        line.getPrice())
    self.assertEqual(request_time, validated_line_1.getStartDate())
    self.assertEqual(stop_date, validated_line_1.getStopDate())

    self.assertTrue(all([q in validated_line_2.getCategoryList() \
        for q in open_sale_order_line_template.getCategoryList()]))
    self.assertEqual(open_sale_order_line_template.getResource(),
        validated_line_2.getResource())
    self.assertEqual(open_sale_order_line_template.getQuantity(),
        line.getQuantity())
    self.assertEqual(open_sale_order_line_template.getPrice(),
        line.getPrice())
    self.assertEqual(request_time_2, validated_line_2.getStartDate())
    self.assertEqual(stop_date_2, validated_line_2.getStopDate())

def withAbort(func):
  @functools.wraps(func)
  def wrapped(self, *args, **kwargs):
    try:
      func(self, *args, **kwargs)
    finally:
      transaction.abort()
  return wrapped

class Simulator:
  def __init__(self, outfile, method, to_return=None):
    self.outfile = outfile
    open(self.outfile, 'w').write(repr([]))
    self.method = method
    self.to_return = to_return

  def __call__(self, *args, **kwargs):
    """Simulation Method"""
    old = open(self.outfile, 'r').read()
    if old:
      l = eval(old)
    else:
      l = []
    l.append({'recmethod': self.method,
      'recargs': args,
      'reckwargs': kwargs})
    open(self.outfile, 'w').write(repr(l))
    return self.to_return

def simulateSimulationMovement_buildSlapOS(func):
  @functools.wraps(func)
  def wrapped(self, *args, **kwargs):
    script_name = 'SimulationMovement_buildSlapOS'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
if context.getTitle() == 'Not visited by SimulationMovement_buildSlapOS':
  context.setTitle('Visited by SimulationMovement_buildSlapOS')
""" )
    transaction.commit()
    try:
      func(self, *args, **kwargs)
    finally:
      if script_name in self.portal.portal_skins.custom.objectIds():
        self.portal.portal_skins.custom.manage_delObjects(script_name)
      transaction.commit()
  return wrapped

class TestAlarm(testSlapOSMixin):
  @simulateSimulationMovement_buildSlapOS
  def test_SimulationMovement_withoutDelivery(self):
    applied_rule = self.portal.portal_simulation.newContent(
        portal_type='Applied Rule')
    simulation_movement = applied_rule.newContent(
        portal_type='Simulation Movement',
        title='Not visited by SimulationMovement_buildSlapOS')
    self.tic()

    self.portal.portal_alarms.slapos_trigger_build.activeSense()
    self.tic()

    self.assertEqual(
        'Visited by SimulationMovement_buildSlapOS',
        simulation_movement.getTitle())

  @simulateSimulationMovement_buildSlapOS
  def test_SimulationMovement_withDelivery(self):
    delivery = self.portal.sale_packing_list_module.newContent(
        portal_type='Sale Packing List')
    delivery_line = delivery.newContent(portal_type='Sale Packing List Line')
    applied_rule = self.portal.portal_simulation.newContent(
        portal_type='Applied Rule')
    simulation_movement = applied_rule.newContent(
        portal_type='Simulation Movement',
        delivery=delivery_line.getRelativeUrl(),
        title='Shall be visited by SimulationMovement_buildSlapOS')
    self.tic()

    self.portal.portal_alarms.slapos_trigger_build.activeSense()
    self.tic()

    self.assertNotEqual(
        'Not visited by SimulationMovement_buildSlapOS',
        simulation_movement.getTitle())

  @withAbort
  def test_SimulationMovement_buildSlapOS(self):
    business_process = self.portal.business_process_module.newContent(
        portal_type='Business Process')
    root_business_link = business_process.newContent(
        portal_type='Business Link')
    business_link = business_process.newContent(portal_type='Business Link')

    root_applied_rule = self.portal.portal_simulation.newContent(
        portal_type='Applied Rule')
    simulation_movement = root_applied_rule.newContent(
        causality=root_business_link.getRelativeUrl(),
        portal_type='Simulation Movement')

    applied_rule = simulation_movement.newContent(portal_type='Applied Rule')
    lower_simulation_movement = applied_rule.newContent(
        causality=business_link.getRelativeUrl(),
        portal_type='Simulation Movement')

    build_simulator = tempfile.mkstemp()[1]
    activate_simulator = tempfile.mkstemp()[1]
    try:
      from Products.CMFActivity.ActiveObject import ActiveObject
      ActiveObject.original_activate = ActiveObject.activate
      ActiveObject.activate = Simulator(activate_simulator, 'activate',
          root_applied_rule)
      from Products.ERP5.Document.BusinessLink import BusinessLink
      BusinessLink.original_build = BusinessLink.build
      BusinessLink.build = Simulator(build_simulator, 'build')

      simulation_movement.SimulationMovement_buildSlapOS(tag='root_tag')

      build_value = eval(open(build_simulator).read())
      activate_value = eval(open(activate_simulator).read())

      self.assertEqual([{
        'recmethod': 'build',
        'recargs': (),
        'reckwargs': {'path': '%s/%%' % root_applied_rule.getPath(),
        'activate_kw': {'tag': 'root_tag'}}}],
        build_value
      )
      self.assertEqual([{
        'recmethod': 'activate',
        'recargs': (),
        'reckwargs': {'tag': 'build_in_progress_%s_%s' % (
            root_business_link.getUid(), root_applied_rule.getUid()),
          'after_tag': 'root_tag', 'activity': 'SQLQueue'}}],
        activate_value)

      open(build_simulator, 'w').truncate()
      open(activate_simulator, 'w').truncate()

      lower_simulation_movement.SimulationMovement_buildSlapOS(tag='lower_tag')
      build_value = eval(open(build_simulator).read())
      activate_value = eval(open(activate_simulator).read())

      self.assertEqual([{
        'recmethod': 'build',
        'recargs': (),
        'reckwargs': {'path': '%s/%%' % root_applied_rule.getPath(),
        'activate_kw': {'tag': 'lower_tag'}}}],
        build_value
      )
      self.assertEqual([{
        'recmethod': 'activate',
        'recargs': (),
        'reckwargs': {'tag': 'build_in_progress_%s_%s' % (
            business_link.getUid(), root_applied_rule.getUid()),
          'after_tag': 'lower_tag', 'activity': 'SQLQueue'}}],
        activate_value)

    finally:
      ActiveObject.activate = ActiveObject.original_activate
      delattr(ActiveObject, 'original_activate')
      BusinessLink.build = BusinessLink.original_build
      delattr(BusinessLink, 'original_build')
      if os.path.exists(build_simulator):
        os.unlink(build_simulator)
      if os.path.exists(activate_simulator):
        os.unlink(activate_simulator)

  @withAbort
  def test_SimulationMovement_buildSlapOS_withDelivery(self):
    delivery = self.portal.sale_packing_list_module.newContent(
        portal_type='Sale Packing List')
    delivery_line = delivery.newContent(portal_type='Sale Packing List Line')
    business_process = self.portal.business_process_module.newContent(
        portal_type='Business Process')
    root_business_link = business_process.newContent(
        portal_type='Business Link')
    business_link = business_process.newContent(portal_type='Business Link')

    root_applied_rule = self.portal.portal_simulation.newContent(
        portal_type='Applied Rule')
    simulation_movement = root_applied_rule.newContent(
        causality=root_business_link.getRelativeUrl(),
        delivery=delivery_line.getRelativeUrl(),
        portal_type='Simulation Movement')

    applied_rule = simulation_movement.newContent(portal_type='Applied Rule')
    lower_simulation_movement = applied_rule.newContent(
        causality=business_link.getRelativeUrl(),
        delivery=delivery_line.getRelativeUrl(),
        portal_type='Simulation Movement')

    build_simulator = tempfile.mkstemp()[1]
    activate_simulator = tempfile.mkstemp()[1]
    try:
      from Products.CMFActivity.ActiveObject import ActiveObject
      ActiveObject.original_activate = ActiveObject.activate
      ActiveObject.activate = Simulator(activate_simulator, 'activate',
          root_applied_rule)
      from Products.ERP5.Document.BusinessLink import BusinessLink
      BusinessLink.original_build = BusinessLink.build
      BusinessLink.build = Simulator(build_simulator, 'build')

      simulation_movement.SimulationMovement_buildSlapOS(tag='root_tag')

      build_value = eval(open(build_simulator).read())
      activate_value = eval(open(activate_simulator).read())

      self.assertEqual([], build_value)
      self.assertEqual([], activate_value)

      open(build_simulator, 'w').write(repr([]))
      open(activate_simulator, 'w').write(repr([]))

      lower_simulation_movement.SimulationMovement_buildSlapOS(tag='lower_tag')
      build_value = eval(open(build_simulator).read())
      activate_value = eval(open(activate_simulator).read())

      self.assertEqual([], build_value)
      self.assertEqual([], activate_value)

    finally:
      ActiveObject.activate = ActiveObject.original_activate
      delattr(ActiveObject, 'original_activate')
      BusinessLink.build = BusinessLink.original_build
      delattr(BusinessLink, 'original_build')
      if os.path.exists(build_simulator):
        os.unlink(build_simulator)
      if os.path.exists(activate_simulator):
        os.unlink(activate_simulator)

class Simulator:
  def __init__(self, outfile, method, to_return=None):
    self.outfile = outfile
    open(self.outfile, 'w').write(repr([]))
    self.method = method
    self.to_return = to_return

  def __call__(self, *args, **kwargs):
    """Simulation Method"""
    old = open(self.outfile, 'r').read()
    if old:
      l = eval(old)
    else:
      l = []
    l.append({'recmethod': self.method,
      'recargs': args,
      'reckwargs': kwargs})
    open(self.outfile, 'w').write(repr(l))
    return self.to_return

def simulateDelivery_manageBuildingCalculatingDelivery(func):
  @functools.wraps(func)
  def wrapped(self, *args, **kwargs):
    script_name = 'Delivery_manageBuildingCalculatingDelivery'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
if context.getTitle() == 'Not visited by Delivery_manageBuildingCalculatingDelivery':
  context.setTitle('Visited by Delivery_manageBuildingCalculatingDelivery')
""" )
    transaction.commit()
    try:
      func(self, *args, **kwargs)
    finally:
      if script_name in self.portal.portal_skins.custom.objectIds():
        self.portal.portal_skins.custom.manage_delObjects(script_name)
      transaction.commit()
  return wrapped

class TestAlarm(testSlapOSMixin):
  @simulateDelivery_manageBuildingCalculatingDelivery
  def _test(self, state, message):
    delivery = self.portal.sale_packing_list_module.newContent(
        title='Not visited by Delivery_manageBuildingCalculatingDelivery',
        portal_type='Sale Packing List')
    self.portal.portal_workflow._jumpToStateFor(delivery, state)
    self.tic()

    self.portal.portal_alarms.slapos_manage_building_calculating_delivery\
        .activeSense()
    self.tic()

    self.assertEqual(message, delivery.getTitle())

  def test_building(self):
    self._test('building', 'Visited by Delivery_manageBuildingCalculatingDelivery')

  def test_calculating(self):
    self._test('calculating', 'Visited by Delivery_manageBuildingCalculatingDelivery')

  def test_diverged(self):
    self._test('diverged', 'Not visited by Delivery_manageBuildingCalculatingDelivery')

  def test_solved(self):
    self._test('solved', 'Not visited by Delivery_manageBuildingCalculatingDelivery')

  @withAbort
  def _test_Delivery_manageBuildingCalculatingDelivery(self, state, empty=False):
    delivery = self.portal.sale_packing_list_module.newContent(
        title='Not visited by Delivery_manageBuildingCalculatingDelivery',
        portal_type='Sale Packing List')
    self.portal.portal_workflow._jumpToStateFor(delivery, state)

    updateCausalityState_simulator = tempfile.mkstemp()[1]
    updateSimulation_simulator = tempfile.mkstemp()[1]
    try:
      from Products.ERP5.Document.Delivery import Delivery
      Delivery.original_updateCausalityState = Delivery\
          .updateCausalityState
      Delivery.updateCausalityState = Simulator(
          updateCausalityState_simulator, 'updateCausalityState')
      Delivery.updateSimulation = Simulator(
          updateSimulation_simulator, 'updateSimulation')

      delivery.Delivery_manageBuildingCalculatingDelivery()

      updateCausalityState_value = eval(open(updateCausalityState_simulator).read())
      updateSimulation_value = eval(open(updateSimulation_simulator).read())

      if empty:
        self.assertEqual([], updateCausalityState_value)
        self.assertEqual([], updateSimulation_value)
      else:
        self.assertEqual([{
          'recmethod': 'updateCausalityState',
          'recargs': (),
          'reckwargs': {'solve_automatically': False}}],
          updateCausalityState_value
        )
        self.assertEqual([{
          'recmethod': 'updateSimulation',
          'recargs': (),
          'reckwargs': {'expand_root': 1, 'expand_related': 1}}],
          updateSimulation_value
        )
    finally:
      Delivery.updateCausalityState = Delivery.original_updateCausalityState
      delattr(Delivery, 'original_updateCausalityState')
      if os.path.exists(updateCausalityState_simulator):
        os.unlink(updateCausalityState_simulator)
      if os.path.exists(updateSimulation_simulator):
        os.unlink(updateSimulation_simulator)

  def test_Delivery_manageBuildingCalculatingDelivery_calculating(self):
    self._test_Delivery_manageBuildingCalculatingDelivery('calculating')

  def test_Delivery_manageBuildingCalculatingDelivery_building(self):
    self._test_Delivery_manageBuildingCalculatingDelivery('building')

  def test_Delivery_manageBuildingCalculatingDelivery_solved(self):
    self._test_Delivery_manageBuildingCalculatingDelivery('solved', True)

  def test_Delivery_manageBuildingCalculatingDelivery_diverged(self):
    self._test_Delivery_manageBuildingCalculatingDelivery('diverged', True)