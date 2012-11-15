# Copyright (c) 2002-2012 Nexedi SA and Contributors. All Rights Reserved.
from Products.SlapOS.tests.testSlapOSMixin import \
  testSlapOSMixin
import transaction
from Products.ERP5Type.tests.utils import createZODBPythonScript
from Products.ERP5Type.tests.backportUnittest import skip

class TestSlapOSAllocation(testSlapOSMixin):

  def _makeSlaveTree(self, requested_template_id='template_slave_instance'):
    super(TestSlapOSAllocation, self).\
        _makeTree(requested_template_id=requested_template_id)

  def test_allocation_no_free_partition(self):
    self._makeTree()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

  def test_allocation_no_host_instance(self):
    self._makeSlaveTree()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

  def _installSoftware(self, computer, url):
    software_installation = self.portal.software_installation_module\
        .template_software_installation.Base_createCloneDocument(batch_mode=1)
    software_installation.edit(url_string=url,
        reference='TESTSOFTINST-%s' % self.generateNewId(),
        aggregate=computer.getRelativeUrl())
    software_installation.validate()
    software_installation.requestStart()
    self.tic()

  def test_allocation_free_partition(self):
    self._makeTree()

    self._makeComputer()
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  def _allocateHost(self, software_instance, computer_partition):
    software_instance.edit(
        aggregate_value=computer_partition
        )
    computer_partition.markBusy()
    self.tic()

  def test_allocation_host_instance(self):
    self._makeSlaveTree()

    self._makeComputer()
    self._allocateHost(self.requested_software_instance,
        self.partition)

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  def test_allocation_capacity_scope_close(self):
    self._makeTree()

    self._makeComputer()
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())
    self.computer.edit(capacity_scope='close')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  def test_allocation_host_capacity_scope_close(self):
    self._makeSlaveTree()

    self._makeComputer()
    self._allocateHost(self.requested_software_instance,
        self.partition)
    self.computer.edit(capacity_scope='close')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  def test_allocation_allocation_scope_close(self):
    self._makeTree()

    self._makeComputer()
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())
    self.computer.edit(allocation_scope='close')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  def test_allocation_host_allocation_scope_close(self):
    self._makeSlaveTree()

    self._makeComputer()
    self._allocateHost(self.requested_software_instance,
        self.partition)
    self.computer.edit(allocation_scope='close')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  def test_allocation_allocation_scope_open_personal(self):
    self._makeTree()

    self._makeComputer()
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())
    self.computer.edit(allocation_scope='open/personal',
      source_administration=self.person_user.getRelativeUrl())
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  def test_allocation_host_allocation_scope_open_personal(self):
    self._makeSlaveTree()

    self._makeComputer()
    self._allocateHost(self.requested_software_instance,
        self.partition)
    self.computer.edit(allocation_scope='open/personal',
      source_administration=self.person_user.getRelativeUrl())
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  def test_allocation_allocation_scope_open_friend(self):
    self._makeTree()

    self._makeComputer()
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())
    # change computer owner
    new_id = self.generateNewId()
    person_user = self.portal.person_module.template_member.\
                                 Base_createCloneDocument(batch_mode=1)
    person_user.edit(
      title="live_test_%s" % new_id,
      reference="live_test_%s" % new_id,
      default_email_text="live_test_%s@example.org" % new_id,
    )

    person_user.validate()
    for assignment in person_user.contentValues(portal_type="Assignment"):
      assignment.open()

    self.computer.edit(
      source_administration=person_user.getRelativeUrl(),
      destination_section=self.person_user.getRelativeUrl(),
      allocation_scope='open/friend')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  def test_allocation_host_allocation_scope_open_friend(self):
    self._makeSlaveTree()

    self._makeComputer()
    self._allocateHost(self.requested_software_instance,
        self.partition)
    # change computer owner
    new_id = self.generateNewId()
    person_user = self.portal.person_module.template_member.\
                                 Base_createCloneDocument(batch_mode=1)
    person_user.edit(
      title="live_test_%s" % new_id,
      reference="live_test_%s" % new_id,
      default_email_text="live_test_%s@example.org" % new_id,
    )

    person_user.validate()
    for assignment in person_user.contentValues(portal_type="Assignment"):
      assignment.open()

    self.computer.edit(
      source_administration=person_user.getRelativeUrl(),
      destination_section=self.person_user.getRelativeUrl(),
      allocation_scope='open/friend')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  def test_allocation_does_not_fail_on_instance_with_damaged_sla_xml(self):
    self._makeTree()

    self.software_instance.setSlaXml('this is not xml')
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    transaction.abort()

  def test_allocation_does_not_fail_on_slave_with_damaged_sla_xml(self):
    self._makeSlaveTree()

    self.software_instance.setSlaXml('this is not xml')
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    transaction.abort()

  def _simulateSoftwareInstance_tryToAllocatePartition(self):
    script_name = 'SoftwareInstance_tryToAllocatePartition'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by SoftwareInstance_tryToAllocatePartition') """ )
    transaction.commit()

  def _dropSoftwareInstance_tryToAllocatePartition(self):
    script_name = 'SoftwareInstance_tryToAllocatePartition'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)
    transaction.commit()

  def test_alarm_software_instance_unallocated(self):
    self._makeTree()

    self._simulateSoftwareInstance_tryToAllocatePartition()
    try:
      self.portal.portal_alarms.slapos_allocate_instance.activeSense()
      self.tic()
    finally:
      self._dropSoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        'Visited by SoftwareInstance_tryToAllocatePartition',
        self.software_instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_slave_instance_unallocated(self):
    self._makeSlaveTree()

    self._simulateSoftwareInstance_tryToAllocatePartition()
    try:
      self.portal.portal_alarms.slapos_allocate_instance.activeSense()
      self.tic()
    finally:
      self._dropSoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        'Visited by SoftwareInstance_tryToAllocatePartition',
        self.software_instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_software_instance_allocated(self):
    self._makeTree()

    self._makeComputer()
    self.software_instance.setAggregate(self.partition.getRelativeUrl())
    self.tic()
    self._simulateSoftwareInstance_tryToAllocatePartition()
    try:
      self.portal.portal_alarms.slapos_allocate_instance.activeSense()
      self.tic()
    finally:
      self._dropSoftwareInstance_tryToAllocatePartition()
    self.assertNotEqual(
        'Visited by SoftwareInstance_tryToAllocatePartition',
        self.software_instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_slave_instance_allocated(self):
    self._makeSlaveTree()

    self._makeComputer()
    self.software_instance.setAggregate(self.partition.getRelativeUrl())
    self.tic()
    self._simulateSoftwareInstance_tryToAllocatePartition()
    try:
      self.portal.portal_alarms.slapos_allocate_instance.activeSense()
      self.tic()
    finally:
      self._dropSoftwareInstance_tryToAllocatePartition()
    self.assertNotEqual(
        'Visited by SoftwareInstance_tryToAllocatePartition',
        self.software_instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_allocation_computer_guid(self):
    self._makeTree()

    self._makeComputer()
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='computer_guid'>%s</parameter>
        </instance>""" % '%s_foo' % self.partition.getParentValue().getReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='computer_guid'>%s</parameter>
        </instance>""" % '%s' % self.partition.getParentValue().getReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  def test_allocation_instance_guid(self):
    self._makeSlaveTree()

    self._makeComputer()
    self._allocateHost(self.requested_software_instance,
        self.partition)

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='instance_guid'>%s</parameter>
        </instance>""" % '%s_foo' % \
        self.requested_software_instance.getReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='instance_guid'>%s</parameter>
        </instance>""" % '%s' % \
        self.requested_software_instance.getReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  def test_allocation_network_guid(self):
    self._makeTree()

    self._makeComputer()
    new_id = self.generateNewId()
    computer_network = self.portal.computer_network_module.newContent(
        portal_type='Computer Network',
        title="live_test_%s" % new_id,
        reference="live_test_%s" % new_id)
    computer_network.validate()
    self.computer.edit(
        subordination_value=computer_network)
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='network_guid'>%s</parameter>
        </instance>""" % '%s_foo' % \
          self.partition.getParentValue().getSubordinationReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='network_guid'>%s</parameter>
        </instance>""" % '%s' % \
          self.partition.getParentValue().getSubordinationReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  def test_allocation_unexpected_sla_parameter(self):
    self._makeTree()

    self._makeComputer()
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='foo'>bar</parameter>
        </instance>""")
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  def check_allocation_category_sla(self, base_category, computer_category,
                                    other_category):
    self._makeTree()

    self._makeComputer()
    self.computer.edit(**{base_category: computer_category})
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

    # Another category
    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='%s'>%s</parameter>
        </instance>""" % (base_category, other_category))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

    # No existing category
    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='%s'>foo</parameter>
        </instance>""" % (base_category))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

    # Computer category
    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='%s'>%s</parameter>
        </instance>""" % (base_category, computer_category))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  def test_allocation_group_sla(self):
    return self.check_allocation_category_sla('group', 'vifib', 'ovh')

  @skip('No category available')
  def test_allocation_cpu_core_sla(self):
    return self.check_allocation_category_sla('cpu_core', 'vifib', 'ovh')

  def test_allocation_cpu_frequency_sla(self):
    return self.check_allocation_category_sla('cpu_frequency', '1000', '2000')

  def test_allocation_cpu_type_sla(self):
    return self.check_allocation_category_sla('cpu_type', 'x86', 'x86/x86_32')

  def test_allocation_local_area_network_type_sla(self):
    return self.check_allocation_category_sla('local_area_network_type', 
                                              'ethernet', 'wifi')

  def test_allocation_memory_size_sla(self):
    return self.check_allocation_category_sla('memory_size', '128', '256')

  def test_allocation_memory_type_sla(self):
    return self.check_allocation_category_sla('memory_type', 'ddr2', 'ddr3')

  def test_allocation_storage_capacity_sla(self):
    return self.check_allocation_category_sla('storage_capacity', 'finite', 
                                              'infinite')

  def test_allocation_storage_interface_sla(self):
    return self.check_allocation_category_sla('storage_interface', 'nas', 'san')

  def test_allocation_storage_redundancy_sla(self):
    return self.check_allocation_category_sla('storage_redundancy', 'dht', 'raid')
