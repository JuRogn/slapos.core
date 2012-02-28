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
    self.Delivery_updateAppliedRule()

@WorkflowMethod.disable
def OpenSaleOrder_migrate(self):
  if self.getSpecialise() != 'sale_trade_condition_module/vifib_simple_trade_condition':
    self.setSpecialise('sale_trade_condition_module/vifib_trade_simple_condition')
  destination = self.getDestination() or self.getDestinationDecision() or self.getDestinationSection()
  assert destination is not None
  if self.getDestinationDecision() != destination:
    self.setDestinationDecision(destination)
  if self.getDestinationSection() != destination:
    self.setDestinationSection(destination)
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
