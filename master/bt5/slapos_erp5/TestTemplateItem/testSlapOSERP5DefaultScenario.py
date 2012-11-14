# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from testSlapOSCloudSecurityGroup import TestSlapOSSecurityMixin
import re
import xml_marshaller
from AccessControl.SecurityManagement import getSecurityManager, \
             setSecurityManager


def changeSkin(skin_name):
  def decorator(func):
    def wrapped(self, *args, **kwargs):
      default_skin = self.portal.portal_skins.default_skin
      self.portal.portal_skins.changeSkin(skin_name)
      self.app.REQUEST.set('portal_skin', skin_name)
      try:
        v = func(self, *args, **kwargs)
      finally:
        self.portal.portal_skins.changeSkin(default_skin)
        self.app.REQUEST.set('portal_skin', default_skin)
      return v
    return wrapped
  return decorator

class TestSlapOSDefaultScenario(TestSlapOSSecurityMixin):
  def joinSlapOS(self, web_site, reference):
    def findMessage(email, body):
      for candidate in reversed(self.portal.MailHost.getMessageList()):
        if email in candidate[1] \
            and body in candidate[2]:
          return candidate[2]

    credential_request_form = self.web_site.ERP5Site_viewCredentialRequestForm()

    self.assertTrue('Vifib Cloud is a distributed cloud around the'
        in credential_request_form)

    email = '%s@example.com' % reference

    request = web_site.ERP5Site_newCredentialRequest(
      reference=reference,
      default_email_text=email
    )

    self.assertTrue('Thanks%20for%20your%20registration.%20You%20will%20be%2'
        '0receive%20an%20email%20to%20activate%20your%20account.' in request)

    self.tic()

    to_click_message = findMessage(email, 'You have requested one user')

    self.assertNotEqual(None, to_click_message)

    to_click_url = re.search('href="(.+?)"', to_click_message).group(1)

    self.assertTrue('ERP5Site_activeLogin' in to_click_url)

    join_key = to_click_url.split('=')[-1]

    web_site.ERP5Site_activeLogin(key=join_key)

    self.tic()

    welcome_message = findMessage(email, "the creation of you new ERP5 account")
    self.assertNotEqual(None, welcome_message)

  def requestComputer(self, title):
    requestXml = self.portal.portal_slap.requestComputer(title)
    self.tic()
    self.assertTrue('marshal' in requestXml)
    computer = xml_marshaller.xml_marshaller.loads(requestXml)
    computer_id = getattr(computer, '_computer_id', None)
    self.assertNotEqual(None, computer_id)
    return computer_id

  def supplySoftware(self, server, url, state='available'):
    self.portal.portal_slap.supplySupply(url, server.getReference(), state)
    self.tic()

    software_installation = self.portal.portal_catalog.getResultValue(
        portal_type='Software Installation',
        url_string=url,
        default_aggregate_uid=server.getUid())

    self.assertNotEqual(None, software_installation)

    if state=='available':
      self.assertEqual('start_requested', software_installation.getSlapState())
    else:
      self.assertEqual('destroy_requested', software_installation.getSlapState())

  @changeSkin('Hosting')
  def setServerOpenPublic(self, server):
    server.Computer_updateAllocationScope(
        allocation_scope='open/public', subject_list=[])
    self.assertEqual('open/public', server.getAllocationScope())
    self.assertEqual('close', server.getCapacityScope())
    server.edit(capacity_scope='open')
    self.tic()

  @changeSkin('Hosting')
  def setServerOpenPersonal(self, server):
    server.Computer_updateAllocationScope(
        allocation_scope='open/personal', subject_list=[])
    self.assertEqual('open/personal', server.getAllocationScope())
    self.assertEqual('open', server.getCapacityScope())
    self.tic()

  @changeSkin('Hosting')
  def setServerOpenFriend(self, server, friend_list=None):
    if friend_list is None:
      friend_list = []
    server.Computer_updateAllocationScope(
        allocation_scope='open/friend', subject_list=friend_list)
    self.assertEqual('open/friend', server.getAllocationScope())
    self.assertEqual('open', server.getCapacityScope())
    self.assertSameSet(friend_list, server.getSubjectList())
    self.tic()

  @changeSkin('Hosting')
  def WebSection_getCurrentHostingSubscriptionList(self):
    return self.web_site.hosting.myspace.my_services\
        .WebSection_getCurrentHostingSubscriptionList()

  def formatComputer(self, computer, partition_count=10):
    computer_dict = dict(
      software_root='/opt',
      reference=computer.getReference(),
      netmask='255.255.255.0',
      address='128.0.0.1',
      instance_root='/srv'
    )
    computer_dict['partition_list'] = []
    a = computer_dict['partition_list'].append
    for i in range(1, partition_count+1):
      a(dict(
        reference='part%s' % i,
        tap=dict(name='tap%s' % i),
        address_list=[
          dict(addr='p%sa1' % i, netmask='p%sn1' % i),
          dict(addr='p%sa2' % i, netmask='p%sn2' % i)
        ]
      ))
    sm = getSecurityManager()
    try:
      self.login(computer.getReference())
      self.portal.portal_slap.loadComputerConfigurationFromXML(
          xml_marshaller.xml_marshaller.dumps(computer_dict))
      self.tic()
      self.assertEqual(partition_count,
          len(computer.contentValues(portal_type='Computer Partition')))
    finally:
      setSecurityManager(sm)

  def simulateSlapgridUR(self, computer):
    sm = getSecurityManager()
    computer_reference = computer.getReference()
    try:
      self.login(computer_reference)
      computer_xml = self.portal.portal_slap.getFullComputerInformation(
          computer_id=computer.getReference())
      slap_computer = xml_marshaller.xml_marshaller.loads(computer_xml)
      self.assertEqual('Computer', slap_computer.__class__.__name__)
      destroyed_partition_id_list = []
      for partition in slap_computer._computer_partition_list:
        if partition._requested_state == 'destroyed' \
              and partition._need_modification == 1:
          self.portal.portal_slap.destroyedComputerPartition(computer.getReference(),
              partition._partition_id
              )
          destroyed_partition_id_list.append(partition._partition_id)
    finally:
      setSecurityManager(sm)
    self.tic()
    self.stepCallSlaposFreeComputerPartitionAlarm()
    self.tic()
    free_partition_id_list = []
    for partition in computer.contentValues(portal_type='Computer Partition'):
      if partition.getReference() in destroyed_partition_id_list \
          and partition.getSlapState() == 'free':
        free_partition_id_list.append(partition.getReference())
    self.assertSameSet(destroyed_partition_id_list, free_partition_id_list)

  def simulateSlapgridCP(self, computer):
    sm = getSecurityManager()
    computer_reference = computer.getReference()
    try:
      self.login(computer_reference)
      computer_xml = self.portal.portal_slap.getFullComputerInformation(
          computer_id=computer.getReference())
      slap_computer = xml_marshaller.xml_marshaller.loads(computer_xml)
      self.assertEqual('Computer', slap_computer.__class__.__name__)
      for partition in slap_computer._computer_partition_list:
        if partition._requested_state in ('started', 'stopped') \
              and partition._need_modification == 1:
          instance_reference = partition._instance_guid
          ip_list = partition._parameter_dict['ip_list']
          connection_xml = xml_marshaller.xml_marshaller.dumps(dict(
            url_1 = 'http://%s/' % ip_list[0][1],
            url_2 = 'http://%s/' % ip_list[1][1],
          ))
          oldsm = getSecurityManager()
          try:
            self.login(instance_reference)
            self.portal.portal_slap.setComputerPartitionConnectionXml(
              computer_id=computer_reference,
              computer_partition_id=partition._partition_id,
              connection_xml=connection_xml
            )
            for slave in partition._parameter_dict['slave_instance_list']:
              slave_reference = slave['slave_reference']
              connection_xml = xml_marshaller.xml_marshaller.dumps(dict(
                url_1 = 'http://%s/%s' % (ip_list[0][1], slave_reference),
                url_2 = 'http://%s/%s' % (ip_list[1][1], slave_reference)
              ))
              self.portal.portal_slap.setComputerPartitionConnectionXml(
                computer_id=computer_reference,
                computer_partition_id=partition._partition_id,
                connection_xml=connection_xml,
                slave_reference=slave_reference
              )

          finally:
            setSecurityManager(oldsm)
    finally:
      setSecurityManager(sm)
    self.tic()

  def personRequestInstanceNotReady(self, **kw):
    response = self.portal.portal_slap.requestComputerPartition(**kw)
    status = getattr(response, 'status', None)
    self.assertEqual(408, status)
    self.tic()

  def personRequestInstance(self, **kw):
    response = self.portal.portal_slap.requestComputerPartition(**kw)
    self.assertTrue(isinstance(response, str))
    software_instance = xml_marshaller.xml_marshaller.loads(response)
    self.assertEqual('SoftwareInstance', software_instance.__class__.__name__)
    self.tic()
    return software_instance

  def checkSlaveInstanceAllocation(self, person_reference, instance_title,
      software_release, software_type, server):

    self.login(person_reference)
    self.personRequestInstanceNotReady(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      shared_xml='<marshal><bool>1</bool></marshal>'
    )

    self.stepCallSlaposAllocateInstanceAlarm()
    self.tic()

    self.personRequestInstance(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      shared_xml='<marshal><bool>1</bool></marshal>'
    )

    # now instantiate it on computer and set some nice connection dict
    self.simulateSlapgridCP(server)

    # let's find instances of user and check connection strings
    hosting_subscription_list = [q.getObject() for q in
        self.WebSection_getCurrentHostingSubscriptionList()
        if q.getTitle() == instance_title]
    self.assertEqual(1, len(hosting_subscription_list))
    hosting_subscription = hosting_subscription_list[0]

    software_instance = hosting_subscription.getPredecessorValue()
    self.assertEqual(software_instance.getTitle(),
        hosting_subscription.getTitle())
    connection_dict = software_instance.getConnectionXmlAsDict()
    self.assertSameSet(('url_1', 'url_2'), connection_dict.keys())
    self.login()
    partition = software_instance.getAggregateValue()
    self.assertSameSet(
        ['http://%s/%s' % (q.getIpAddress(), software_instance.getReference())
            for q in partition.contentValues(
                portal_type='Internet Protocol Address')],
        connection_dict.values())

  def checkSlaveInstanceUnallocation(self, person_reference, instance_title,
      software_release, software_type, server):

    self.login(person_reference)
    self.personRequestInstanceNotReady(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      shared_xml='<marshal><bool>1</bool></marshal>',
      state='<marshal><string>destroyed</string></marshal>'
    )

    # let's find instances of user and check connection strings
    hosting_subscription_list = [q.getObject() for q in
        self.WebSection_getCurrentHostingSubscriptionList()
        if q.getTitle() == instance_title]

    self.assertEqual(0, len(hosting_subscription_list))

  def checkInstanceUnallocation(self, person_reference, instance_title,
      software_release, software_type, server):

    self.login(person_reference)
    self.personRequestInstanceNotReady(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
      state='<marshal><string>destroyed</string></marshal>'
    )

    # now instantiate it on computer and set some nice connection dict
    self.simulateSlapgridUR(server)

    # let's find instances of user and check connection strings
    hosting_subscription_list = [q.getObject() for q in
        self.WebSection_getCurrentHostingSubscriptionList()
        if q.getTitle() == instance_title]
    self.assertEqual(0, len(hosting_subscription_list))

  def checkInstanceAllocation(self, person_reference, instance_title,
      software_release, software_type, server):

    self.login(person_reference)
    self.personRequestInstanceNotReady(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
    )

    self.stepCallSlaposAllocateInstanceAlarm()
    self.tic()

    self.personRequestInstance(
      software_release=software_release,
      software_type=software_type,
      partition_reference=instance_title,
    )

    # now instantiate it on computer and set some nice connection dict
    self.simulateSlapgridCP(server)

    # let's find instances of user and check connection strings
    hosting_subscription_list = [q.getObject() for q in
        self.WebSection_getCurrentHostingSubscriptionList()
        if q.getTitle() == instance_title]
    self.assertEqual(1, len(hosting_subscription_list))
    hosting_subscription = hosting_subscription_list[0]

    software_instance = hosting_subscription.getPredecessorValue()
    self.assertEqual(software_instance.getTitle(),
        hosting_subscription.getTitle())
    connection_dict = software_instance.getConnectionXmlAsDict()
    self.assertSameSet(('url_1', 'url_2'), connection_dict.keys())
    self.login()
    partition = software_instance.getAggregateValue()
    self.assertSameSet(
        ['http://%s/' % q.getIpAddress() for q in
            partition.contentValues(portal_type='Internet Protocol Address')],
        connection_dict.values())

  def assertHostingSubscriptionSimulationCoverage(self, subscription,
      level=1):
    self.login()
    applied_rule_list = self.portal.portal_catalog(portal_type='Applied Rule',
        causality_uid=subscription.getUid())
    self.assertEqual(1, len(applied_rule_list))
    applied_rule = applied_rule_list[0]
    simulation_movement_list = applied_rule.contentValues(
        portal_type='Simulation Movement')
    self.assertNotEqual(0, len(simulation_movement_list))

    open_sale_order_line_template = self.portal.restrictedTraverse(
        self.portal.portal_preferences.getPreferredOpenSaleOrderLineTemplate())
    for simulation_movement in simulation_movement_list:
      self.assertEqual(open_sale_order_line_template.getResource(),
          simulation_movement.getResource())
      self.assertEqual(subscription.getRelativeUrl(),
          simulation_movement.getAggregate())
      self.assertEqual(subscription.getPeriodicityMonthDay(),
          simulation_movement.getStartDate().day())
      self.assertEqual(subscription.getPeriodicityMonthDay(),
          simulation_movement.getStopDate().day())
      applied_rule_list_l2 = simulation_movement.contentValues(
          portal_type='Applied Rule')
      if level == 1:
        self.assertEqual(0, len(applied_rule_list_l2))
      else:
        raise NotImplementedError

  def assertOpenSaleOrderCoverage(self, person_reference):
    self.login()
    person = self.portal.portal_catalog.getResultValue(portal_type='Person',
        reference=person_reference)
    hosting_subscription_list = self.portal.portal_catalog(
        portal_type='Hosting Subscription',
        default_destination_section_uid=person.getUid()
    )

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_section_uid=person.getUid(),
        validation_state='validated'
    )

    if len(hosting_subscription_list) == 0:
      self.assertEqual(0, len(open_sale_order_list))
      return

    self.assertEqual(1, len(open_sale_order_list))
    open_sale_order = open_sale_order_list[0]
    line_list = open_sale_order.contentValues(
        portal_type='Open Sale Order Line')

    self.assertEqual(len(hosting_subscription_list), len(line_list))

    self.assertSameSet(
        [q.getRelativeUrl() for q in hosting_subscription_list],
        [q.getAggregate() for q in line_list]
    )


  def test(self):
    # some preparation
    self.logout()
    self.web_site = self.portal.web_site_module.hosting

    # lets join as owner, which will own few computers
    owner_reference = 'owner-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, owner_reference)

    # hooray, now it is time to create computers
    self.login(owner_reference)

    public_server_title = 'Public Server for %s' % owner_reference
    public_server_id = self.requestComputer(public_server_title)
    public_server = self.portal.portal_catalog.getResultValue(
        portal_type='Computer', reference=public_server_id)
    self.assertNotEqual(None, public_server)
    self.setServerOpenPublic(public_server)

    personal_server_title = 'Personal Server for %s' % owner_reference
    personal_server_id = self.requestComputer(personal_server_title)
    personal_server = self.portal.portal_catalog.getResultValue(
        portal_type='Computer', reference=personal_server_id)
    self.assertNotEqual(None, personal_server)
    self.setServerOpenPersonal(personal_server)

    friend_server_title = 'Friend Server for %s' % owner_reference
    friend_server_id = self.requestComputer(friend_server_title)
    friend_server = self.portal.portal_catalog.getResultValue(
        portal_type='Computer', reference=friend_server_id)
    self.assertNotEqual(None, friend_server)
    self.setServerOpenFriend(friend_server)

    # and install some software on them
    public_server_software = self.generateNewSoftwareReleaseUrl()
    self.supplySoftware(public_server, public_server_software)

    personal_server_software = self.generateNewSoftwareReleaseUrl()
    self.supplySoftware(personal_server, personal_server_software)

    friend_server_software = self.generateNewSoftwareReleaseUrl()
    self.supplySoftware(friend_server, friend_server_software)

    # format the computers
    self.formatComputer(public_server)
    self.formatComputer(personal_server)
    self.formatComputer(friend_server)

    # join as the another visitor and request software instance on public
    # computer
    self.logout()
    public_reference = 'public-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, public_reference)

    public_instance_title = 'Public title %s' % self.generateNewId()
    public_instance_type = 'public type'
    self.checkInstanceAllocation(public_reference, public_instance_title,
        public_server_software, public_instance_type, public_server)

    # join as owner friend and request a software instance on computer
    # configured by owner

    self.logout()
    friend_reference = 'friend-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, friend_reference)
    self.login()
    friend_email = self.portal.portal_catalog.getResultValue(
        portal_type='Person', reference=friend_reference).getDefaultEmailText()

    # allow friend to alloce on friendly computer
    self.login(owner_reference)
    self.setServerOpenFriend(friend_server, [friend_email])

    friend_instance_title = 'Friend title %s' % self.generateNewId()
    friend_instance_type = 'friend_type'
    self.checkInstanceAllocation(friend_reference, friend_instance_title,
        friend_server_software, friend_instance_type, friend_server)

    # check that friend is able to request slave instance matching the
    # public's computer software instance
    friend_slave_instance_title = 'Friend slave title %s' % self.\
        generateNewId()
    self.checkSlaveInstanceAllocation(friend_reference,
        friend_slave_instance_title, public_server_software,
        public_instance_type, public_server)

    # turn public guy to a friend and check that he can allocate slave
    # instance on instance provided by friend

    self.login()
    public_email = self.portal.portal_catalog.getResultValue(
        portal_type='Person', reference=public_reference).getDefaultEmailText()
    self.login(owner_reference)
    self.setServerOpenFriend(friend_server, [friend_email, public_email])

    public_slave_instance_title = 'Public slave title %s' % self\
        .generateNewId()
    self.checkSlaveInstanceAllocation(public_reference,
        public_slave_instance_title, friend_server_software,
        friend_instance_type, friend_server)

    # now deallocate the slaves
    self.checkSlaveInstanceUnallocation(public_reference,
        public_slave_instance_title, friend_server_software,
        friend_instance_type, friend_server)

    self.checkSlaveInstanceUnallocation(friend_reference,
        friend_slave_instance_title, public_server_software,
        public_instance_type, public_server)

    # and the instances
    self.checkInstanceUnallocation(public_reference, public_instance_title,
        public_server_software, public_instance_type, public_server)

    self.checkInstanceUnallocation(friend_reference, friend_instance_title,
        friend_server_software, friend_instance_type, friend_server)

    # check the Open Sale Order coverage
    self.stepCallSlaposRequestUpdateHostingSubscriptionOpenSaleOrderAlarm()
    self.tic()

    self.login()

    self.assertOpenSaleOrderCoverage(owner_reference)
    self.assertOpenSaleOrderCoverage(friend_reference)
    self.assertOpenSaleOrderCoverage(public_reference)

    # check the Subscription Simulation

    self.stepCallUpdateOpenOrderSimulationAlarm()
    self.tic()

    for person_reference in (owner_reference, friend_reference,
        public_reference):
      person = self.portal.portal_catalog.getResultValue(portal_type='Person',
          reference=person_reference)
      for subscription in self.portal.portal_catalog(
          portal_type='Hosting Subscription',
          default_destination_section_uid=person.getUid()):
        self.assertHostingSubscriptionSimulationCoverage(
            subscription.getObject())
