from DateTime import DateTime
from Products.ERP5Type.Base import WorkflowMethod

@WorkflowMethod.disable
def DeliveryLineSetZeroPriceAndOrUpdateAppliedRule(self):
  portal_type = self.getPortalType()
  assert( portal_type in self.getPortalDeliveryMovementTypeList())
  common_specialise = 'sale_trade_condition_module/vifib_simple_trade_condition'
  delivery = self.getParentValue()
  price_currency = 'currency_module/EUR'
  if delivery.getPortalType() in ['Purchase Packing List', 'Sale Packing List']:
    specialise = delivery.getSpecialise()
    if common_specialise != specialise:
      delivery.setSpecialise(common_specialise)
    delivery.SalePackingList_setArrow()
    if delivery.getPriceCurrency() != price_currency:
      delivery.setPriceCurrency(price_currency)
  self.setPrice(0.0)
  if self.getSimulationState() == 'cancelled':
    # force no simulation
    self.setQuantity(0.0)
  else:
    self.setQuantity(1.0)

@WorkflowMethod.disable
def OpenSaleOrder_migrate(self):
  if self.getSpecialise() != 'sale_trade_condition_module/vifib_simple_trade_condition':
    self.setSpecialise('sale_trade_condition_module/vifib_simple_trade_condition')
  destination = self.getDestination() or self.getDestinationDecision() or self.getDestinationSection()
  assert destination is not None
  if self.getDestinationDecision() != destination:
    self.setDestinationDecision(destination)
  if self.getDestinationSection() != destination:
    self.setDestinationSection(destination)
  if self.getDestination() != destination:
    self.setDestination(destination)
  if self.getSource() != 'organisation_module/vifib_internet':
    self.setSource('organisation_module/vifib_internet')
  if self.getSourceSection() != 'organisation_module/vifib_internet':
    self.setSourceSection('organisation_module/vifib_internet')
  if self.getPriceCurrency() != 'currency_module/EUR':
    self.setPriceCurrency('currency_module/EUR')

@WorkflowMethod.disable
def OpenSaleOrderLine_migrate(self):
  now = DateTime().earliestTime()
  self.setStartDate(now)
  self.setStopDate(now)
  self.setPrice(0.0)
  self.setQuantity(1.0)
  self.setResource(self.getPortalObject().portal_preferences.getPreferredInstanceSubscriptionResource())
  resource_value = self.getResourceValue()
  self.setBaseContributionList(resource_value.getBaseContributionList())
  self.setUseList(resource_value.getUseList())
  self.setQuantityUnit(resource_value.getQuantityUnit())
  self.setSpecialise(None)
  self.setDestination(None)
  self.setDestinationSection(None)
  self.setDestinationDecision(None)
  self.setPriceCurrency(None)
  self.setSource(None)
  self.setSourceSection(None)
  self.setSourceDecision(None)

@WorkflowMethod.disable
def VifibSaleInvoiceBuilder_buildAndPlan(self, movement_list):
  delivery_list = self.build(movement_list=movement_list)
  wf = self.getPortalObject().portal_workflow.accounting_workflow
  plan_tdef = wf.transitions.get("plan")
  for delivery in delivery_list:
    if delivery.getSimulationState() == 'draft':
      wf._changeStateOf(delivery, plan_tdef, dict(comment="Generated by the upgrade"))

def fixSaleOrder(slap_document):
  sale_order_line_list = slap_document.getAggregateRelatedValueList(
    portal_type='Sale Order Line')
  assert(len(sale_order_line_list) == 1)
  sale_order = sale_order_line_list[0].getParentValue()
  sale_packing_list_line_list = slap_document.getAggregateRelatedValueList(
    portal_type='Sale Packing List Line')
  if len(sale_packing_list_line_list) == 0:
    return sale_order.contentValues(portal_type='Sale Order Line')[0]
  assert(len(sale_packing_list_line_list) == 1)
  sale_packing_list = sale_packing_list_line_list[0].getParentValue()

  new_sale_order = sale_order.Base_createCloneDocument(batch_mode=1)
  slap_document.getPortalObject().portal_workflow.\
    _jumpToStateFor(new_sale_order, 'ordered', 'order_workflow')
  applied_rule = sale_order.getCausalityRelatedValue(portal_type='Applied Rule')
  applied_rule.getParentValue().deleteContent(applied_rule.getId())
  sale_order.getParentValue().deleteContent(sale_order.getId())
  sale_packing_list.getParentValue().deleteContent(sale_packing_list.getId())
  return new_sale_order.contentValues(portal_type='Sale Order Line')[0]

def SlapDocument_migrateSlapState(self):
  @WorkflowMethod.disable
  def real(self):
    from Products.ZSQLCatalog.SQLCatalog import Query, ComplexQuery
    
    def setUpPeriodicity(hosting_subscription):
      from Products.ERP5Type.DateUtils import addToDate, getClosestDate
      start_date = hosting_subscription.getCreationDate()
      start_date = getClosestDate(target_date=start_date, precision='day')
      while start_date.day() >= 29:
        start_date = addToDate(start_date, to_add={'day': -1})
      periodicity_month_day_list = [start_date.day()]
      periodicity_hour_list=[0]
      periodicity_minute_list=[0]
      hosting_subscription.edit(
        periodicity_month_day_list=periodicity_month_day_list,
        periodicity_hour_list=periodicity_hour_list,
        periodicity_minute_list=periodicity_minute_list
      )
    
    slap_document = self
    portal = self.getPortalObject()
    
    portal_type_list = ('Hosting Subscription', 'Software Instance', 'Slave Instance')
    portal_type = slap_document.getPortalType()
    if portal_type not in portal_type_list:
      raise TypeError('%s is not %s' % (slap_document.getPath(), portal_type_list))
    
    explanation_delivery_line = portal.portal_catalog.getResultValue(
      portal_type='Sale Packing List Line',
      simulation_state=['ready', 'confirmed', 'started', 'stopped', 'delivered'],
      query=ComplexQuery(
        Query(default_aggregate_uid=slap_document.getUid()),
        Query(default_resource_uid=[
          portal.restrictedTraverse(portal.portal_preferences.getPreferredInstanceSetupResource()).getUid(),
          portal.restrictedTraverse(portal.portal_preferences.getPreferredInstanceHostingResource()).getUid(),
          portal.restrictedTraverse(portal.portal_preferences.getPreferredInstanceCleanupResource()).getUid(),
    ]),
        operator='AND',
      ),
      sort_on=(('movement.start_date', 'DESC'),)
    )
    if explanation_delivery_line is None:
      explanation_delivery_line = slap_document.getAggregateRelatedValue(portal_type='Sale Order Line')
    
    if slap_document.getRelativeUrl() == 'hosting_subscription_module/20120521-C46CA2':
      # special case of destroyed data
      explanation_delivery_line = fixSaleOrder(slap_document)
    
    if portal_type == 'Hosting Subscription':
      current_periodicity = slap_document.getPeriodicityMonthDayList()
      if current_periodicity is None or len(current_periodicity) == 0:
        setUpPeriodicity(slap_document)
      # Person is now directly associated on the HS
      slap_document.edit(
        destination_section_value=explanation_delivery_line.getDestinationSectionValue(portal_type="Person"),
      )
      assert(slap_document.getDestinationSection() == explanation_delivery_line.getDestinationSectionValue().getRelativeUrl())
    else:
      hosting_subscription = explanation_delivery_line.getAggregateValue(portal_type='Hosting Subscription')
      slap_document.edit(
        specialise_value=hosting_subscription,
        root_software_release_url=explanation_delivery_line.getAggregateValue(portal_type='Software Release').getUrlString()
      )
      assert(slap_document.getSpecialise() == hosting_subscription.getRelativeUrl())
    
    
    # Migrate slap state
    if portal_type == 'Hosting Subscription':
      state = slap_document.getRootState()
      promise_kw = {
        'instance_xml': slap_document.getTextContent(),
        'software_type': slap_document.getSourceReference(),
        'sla_xml': slap_document.getSlaXml(),
        'software_release': slap_document.getRootSoftwareReleaseUrl(),
        'shared': slap_document.isRootSlave()
      }
    else:
      if explanation_delivery_line.getPortalType() == 'Sale Packing List Line':
        resource = explanation_delivery_line.getResource()
        if resource == portal.portal_preferences.getPreferredInstanceSetupResource():
          state = 'stopped'
        elif resource == portal.portal_preferences.getPreferredInstanceCleanupResource():
          state = 'destroyed'
        elif resource == portal.portal_preferences.getPreferredInstanceHostingResource():
          if explanation_delivery_line.getSimulationState() in ('confirmed', 'started'):
            state = 'started'
          else:
            state = 'stopped'
          pass
        else:
          raise TypeError('Bad resource %s' % resource)
        pass
      else:
        if explanation_delivery_line.getSimulationState() == 'cancelled':
          state = 'destroyed'
        else:
          assert(explanation_delivery_line.getSimulationState() in ['ordered', 'confirmed'])
          previous_workflow_state = self.workflow_history[
            'software_instance_slap_interface_workflow'][-1]['slap_state']
          if previous_workflow_state == 'start_requested':
            state = 'started'
          elif previous_workflow_state == 'stop_requested':
            state = 'stopped'
          else:
            raise NotImplementedError("Previous state %r not supported" % previous_workflow_state)
      promise_kw = {
        'instance_xml': slap_document.getTextContent(),
        'software_type': slap_document.getSourceReference(),
        'sla_xml': slap_document.getSlaXml(),
        'software_release': slap_document.getRootSoftwareReleaseUrl(),
        'shared': slap_document.getPortalType() == 'Slave Instance'
      }
    
      slap_document.setCausalityValue(explanation_delivery_line.getParentValue())
      if state != 'destroyed' or explanation_delivery_line.getSimulationState() != 'delivered':
        slap_document.setAggregateValue(explanation_delivery_line.getAggregateValue(portal_type='Computer Partition'))
        assert(slap_document.getAggregate() == explanation_delivery_line.getAggregate(portal_type='Computer Partition'))
    state_map = {
      'started': 'start_requested',
      'stopped': 'stop_requested',
      'destroyed': 'destroy_requested'
    }
    required_state = state_map[state]
    _jumpToStateFor = portal.portal_workflow._jumpToStateFor
    if slap_document.getSlapState() != required_state:
        _jumpToStateFor(slap_document, required_state, 'instance_slap_interface_workflow')
    if not(slap_document.getSlapState() == required_state):
      raise ValueError('%s: %s != %s' % (state, slap_document.getSlapState(), required_state))
    
    # Migrate validation state
    if portal_type == 'Hosting Subscription':
      if state == 'destroyed':
        _jumpToStateFor(slap_document, 'archived', 'hosting_subscription_workflow')
        assert(slap_document.getValidationState() == 'archived')
      else:
        _jumpToStateFor(slap_document, 'validated', 'hosting_subscription_workflow')
        assert(slap_document.getValidationState() == 'validated')
    else:
      if state == 'destroyed' and \
          (explanation_delivery_line.getPortalType() == 'Sale Order Line' or \
          explanation_delivery_line.getSimulationState() == 'delivered'):
        _jumpToStateFor(slap_document, 'invalidated', 'item_workflow')
      else:
        if not(slap_document.getValidationState() == 'validated'):
          raise ValueError('%s != %s' % (slap_document.getValidationState(), 'validated'))

    # Update Local Roles
    slap_document.updateLocalRolesOnSecurityGroups()
  real(self)

def HostingSubscription_garbageCollectForMigration(self):
  @WorkflowMethod.disable
  def real(self):
    slap_document = self
    portal = self.getPortalObject()

    title = slap_document.getTitle()
    instance_state = 'destroy_requested'
    for software_instance in slap_document.getPredecessorValueList():
      if software_instance.getTitle() == title:
        if software_instance.getSlapState() != 'destroy_requested':
          instance_state = software_instance.getSlapState()
          break

    if instance_state == 'destroy_requested':
      _jumpToStateFor = portal.portal_workflow._jumpToStateFor
      _jumpToStateFor(slap_document, instance_state, 'instance_slap_interface_workflow')
      assert(slap_document.getSlapState() == instance_state)
      _jumpToStateFor(slap_document, 'archived', 'hosting_subscription_workflow')
      assert(slap_document.getValidationState() == 'archived')

    # Update Local Roles
    slap_document.updateLocalRolesOnSecurityGroups()
  real(self)
  
def SalePackingListLine_deliver(self):
  @WorkflowMethod.disable
  def real(self):
    portal = self.getPortalObject()
    assert(self.getResource() in [portal.portal_preferences.getPreferredInstanceSetupResource(),
      portal.portal_preferences.getPreferredInstanceUpdateResource()])
    if self.getSimulationState() != 'delivered':
      portal.portal_workflow._jumpToStateFor(self.getParentValue(), 'delivered')
      self.recursiveReindexObject()
  real(self)

def Computer_updateLocalRoles(self):
  self.updateLocalRolesOnSecurityGroups(reindex=False)
  for partition in self.contentValues(portal_type='Computer Partition'):
    partition.updateLocalRolesOnSecurityGroups(reindex=False)

def Instance_migrateRootSoftwareReleaseUrl(self):
  @WorkflowMethod.disable
  def real(self):
    if self.getPortalType() not in ('Hosting Subscription', 'Software Instance'):
      raise TypeError('%s type is not supported' % self.getPortalType())
    if 'root_software_release_url' in self.__dict__:
      self.url_string = self.root_software_release_url
      delattr(self, 'root_software_release_url')
  real(self)
