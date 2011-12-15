import unittest
from Products.ERP5Type.tests.Sequence import SequenceList
from Products.ERP5Type.DateUtils import getClosestDate, addToDate
from testVifibSlapWebService import TestVifibSlapWebServiceMixin

from DateTime.DateTime import DateTime

class TestVifibOpenOrderSimulation(TestVifibSlapWebServiceMixin):

  def stepCheckSimulationMovement(self, sequence, **kw):
    # find related documents: open order, open order line,
    # subscription item, etc.
    person = self.portal.person_module['test_vifib_customer']
    open_order = \
      person.getDestinationDecisionRelatedValue(portal_type="Open Sale Order")
    open_order_line_list = \
      open_order.contentValues(portal_type="Open Sale Order Line")
    self.assertEquals(1, len(open_order_line_list))
    open_order_line = open_order_line_list[0]
    hosting_subscription = \
      open_order_line.getAggregateValue(portal_type="Hosting Subscription")
    applied_rule = \
      hosting_subscription.getCausalityRelatedValue(portal_type="Applied Rule")
    self.assertEquals(
      "portal_rules/default_subscription_item_rule",
      applied_rule.getSpecialise())

    # check periodicity, should be first day of each month
    self.assertEquals(
      None, hosting_subscription.getPeriodicityMinuteFrequency())
    self.assertEquals(
      [0], hosting_subscription.getPeriodicityMinuteList())
    self.assertEquals(
      None, hosting_subscription.getPeriodicityHourFrequency())
    self.assertEquals(
      [0], hosting_subscription.getPeriodicityHourList())
    self.assertEquals(
      None, hosting_subscription.getPeriodicityDayFrequency())
    self.assertEquals(
      None, hosting_subscription.getPeriodicityMonthFrequency())
    self.assertEquals(
      [1], hosting_subscription.getPeriodicityMonthDayList())
    self.assertEquals(
      None, hosting_subscription.getPeriodicityWeekFrequency())

    # check start date and stop date of the subscription item,
    # currently there are 12 months
    now = DateTime()
    start_date = \
      getClosestDate(target_date=now, precision='day', before=1)
    self.assertEquals(
      start_date.year(), open_order_line.getStartDate().year())
    self.assertEquals(
      start_date.month(), open_order_line.getStartDate().month())
    self.assertEquals(
      start_date.day(), open_order_line.getStartDate().day())
    self.assertEquals(
      0, open_order_line.getStartDate().hour())
    self.assertEquals(
      0, open_order_line.getStartDate().minute())
    self.assertEquals(
      0.0, open_order_line.getStartDate().second())
    stop_date = addToDate(
      getClosestDate(target_date=now, precision='month', before=1), year=1)
    self.assertEquals(
      stop_date.year(), open_order_line.getStopDate().year())
    self.assertEquals(
      stop_date.month(), open_order_line.getStopDate().month())
    self.assertEquals(
      stop_date.day(), open_order_line.getStopDate().day())
    self.assertEquals(
      0, open_order_line.getStopDate().hour())
    self.assertEquals(
      0, open_order_line.getStopDate().minute())
    self.assertEquals(
      0.0, open_order_line.getStopDate().second())

    # Calculate the list of time frames
    expected_time_frame_list = [start_date]
    current = \
      getClosestDate(target_date=start_date, precision='month', before=0)
    if start_date == current:
      current = addToDate(start_date, month=1)
    while current <= stop_date:
      expected_time_frame_list.append(current)
      current = addToDate(
        getClosestDate(target_date=current, precision='month', before=0),
        month=1)

    # Check that simulation is created by the periodicity
    self.assertEquals(len(expected_time_frame_list),
                      len(applied_rule.contentValues()) + 1)

    # Check the list of expected simulation
    idx = 0
    while idx + 1 < len(expected_time_frame_list):
      # select simulation given start_date and stop_date
      simulation_movement_list = \
        self.portal.portal_catalog.unrestrictedSearchResults(
          parent_uid=applied_rule.getUid(),
          portal_type="Simulation Movement",
          **{
            'movement.start_date':expected_time_frame_list[idx],
            'movement.stop_date':expected_time_frame_list[idx + 1],
          })
      self.assertEquals(1, len(simulation_movement_list))
      simulation_movement = simulation_movement_list[0].getObject()
      self.assertNotEquals(None, simulation_movement)

      # Check simulation movement property
      self.assertEquals(1.0,
        simulation_movement.getQuantity())
      self.assertEquals("unit/piece",
        simulation_movement.getQuantityUnit())
      self.assertEquals(1.0,
        simulation_movement.getPrice())
      self.assertEquals("currency_module/EUR",
        simulation_movement.getPriceCurrency())
      # XXX supplier
      self.assertEquals("organisation_module/vifib_internet",
        simulation_movement.getSource())
      self.assertEquals("organisation_module/vifib_internet",
        simulation_movement.getSourceSection())
      # XXX customer
      self.assertEquals("person_module/test_vifib_customer",
        simulation_movement.getDestination())
      self.assertEquals("person_module/test_vifib_customer",
        simulation_movement.getDestinationSection())
      self.assertEquals(open_order_line.getSpecialise(),
        simulation_movement.getSpecialise())
      self.assertEquals("service_module/vifib_instance_subscription",
        simulation_movement.getResource())
      self.assertEquals("default/delivery",
        simulation_movement.getTradePhase())
      self.assertEquals(None,
                           simulation_movement.getAggregate(
                             portal_type="Computer Partition"))
      self.assertEquals(None,
                           simulation_movement.getAggregate(
                             portal_type="Software Instance"))
      self.assertEquals(hosting_subscription.getRelativeUrl(),
                           simulation_movement.getAggregate(
                             portal_type="Hosting Subscription"))
      self.assertEquals(None,
                           simulation_movement.getAggregate(
                             portal_type="Software Release"))

      # fetch invoice level simulation
      applied_rule_invoice_list = \
        simulation_movement.contentValues(portal_type="Applied Rule")
      self.assertEquals(1, len(applied_rule_invoice_list))
      applied_rule_invoice = \
        applied_rule_invoice_list[0].getObject()
      self.assertNotEquals(None, applied_rule_invoice)
      simulation_movement_invoice_list = \
        applied_rule_invoice.contentValues(portal_type="Simulation Movement")
      self.assertEquals(1, len(simulation_movement_invoice_list))
      simulation_movement_invoice = \
        simulation_movement_invoice_list[0].getObject()
      self.assertNotEquals(None, simulation_movement_invoice)

      # check property of invoice simulation
      self.assertEquals(1.0,
        simulation_movement_invoice.getQuantity())
      self.assertEquals("unit/piece",
        simulation_movement_invoice.getQuantityUnit())
      self.assertEquals(1.0,
        simulation_movement_invoice.getPrice())
      self.assertEquals("currency_module/EUR",
        simulation_movement_invoice.getPriceCurrency())
      self.assertEquals("organisation_module/vifib_internet",
        simulation_movement_invoice.getSource())
      self.assertEquals("organisation_module/vifib_internet",
        simulation_movement_invoice.getSourceSection())
      self.assertEquals("person_module/test_vifib_customer",
        simulation_movement_invoice.getDestination())
      self.assertEquals("person_module/test_vifib_customer",
        simulation_movement_invoice.getDestinationSection())
      self.assertEquals(open_order_line.getSpecialise(),
        simulation_movement_invoice.getSpecialise())
      self.assertEquals("service_module/vifib_instance_subscription",
        simulation_movement_invoice.getResource())
      self.assertEquals("default/invoicing",
        simulation_movement_invoice.getTradePhase())
      self.assertEquals(expected_time_frame_list[idx+1],
        simulation_movement_invoice.getStartDate())
      self.assertEquals(expected_time_frame_list[idx+1],
        simulation_movement_invoice.getStopDate())
      self.assertEquals(None,
                        simulation_movement_invoice.getAggregate(
                          portal_type="Computer Partition"))
      self.assertEquals(None,
                        simulation_movement_invoice.getAggregate(
                          portal_type="Software Instance"))
      self.assertEquals(hosting_subscription.getRelativeUrl(),
                        simulation_movement_invoice.getAggregate(
                          portal_type="Hosting Subscription"))
      self.assertEquals(None,
                        simulation_movement_invoice.getAggregate(
                          portal_type="Software Release"))

      # fetch invoice transaction level simulation, there are 2:
      # credit and debit, and resource should be currency
      applied_rule_invoice_transaction_list = \
        simulation_movement_invoice.contentValues(portal_type="Applied Rule")
      self.assertEquals(1, len(applied_rule_invoice_transaction_list))
      applied_rule_invoice_transaction = \
        applied_rule_invoice_transaction_list[0].getObject()
      self.assertNotEquals(None, applied_rule_invoice_transaction)
      simulation_movement_invoice_transaction_list = \
        applied_rule_invoice_transaction.contentValues(
          portal_type="Simulation Movement")
      self.assertEquals(2, len(simulation_movement_invoice_transaction_list))
      simulation_movement_invoice_transaction_credit = None
      simulation_movement_invoice_transaction_debit = None
      for simulation_movement_invoice_transaction in \
        simulation_movement_invoice_transaction_list:
        if "business_process_module/erp5_default_business_process/account_credit_path" \
          in simulation_movement_invoice_transaction.getCausalityList():
            simulation_movement_invoice_transaction_credit = \
              simulation_movement_invoice_transaction.getObject()
        if "business_process_module/erp5_default_business_process/account_debit_path" \
          in simulation_movement_invoice_transaction.getCausalityList():
            simulation_movement_invoice_transaction_debit = \
              simulation_movement_invoice_transaction.getObject()
      self.assertNotEquals(None, simulation_movement_invoice_transaction_credit)
      self.assertNotEquals(None, simulation_movement_invoice_transaction_debit)

      # check property of invoice transaction simulation
      self.assertEquals(-1.0,
        simulation_movement_invoice_transaction_credit.getQuantity())
      self.assertEquals("unit/piece",
        simulation_movement_invoice_transaction_credit.getQuantityUnit())
      self.assertEquals(1.0,
        simulation_movement_invoice_transaction_credit.getPrice())
      self.assertEquals(None,
        simulation_movement_invoice_transaction_credit.getPriceCurrency())
      self.assertEquals("account_module/sales",
        simulation_movement_invoice_transaction_credit.getSource())
      self.assertEquals("organisation_module/vifib_internet",
        simulation_movement_invoice_transaction_credit.getSourceSection())
      self.assertEquals("account_module/purchase",
        simulation_movement_invoice_transaction_credit.getDestination())
      self.assertEquals("person_module/test_vifib_customer",
        simulation_movement_invoice_transaction_credit.getDestinationSection())
      self.assertEquals("currency_module/EUR",
        simulation_movement_invoice_transaction_credit.getResource())
      self.assertEquals(open_order_line.getSpecialise(),
        simulation_movement_invoice_transaction_credit.getSpecialise())
      self.assertEquals("default/accounting",
        simulation_movement_invoice_transaction_credit.getTradePhase())
      self.assertEquals(expected_time_frame_list[idx+1],
        simulation_movement_invoice_transaction_credit.getStartDate())
      self.assertEquals(expected_time_frame_list[idx+1],
        simulation_movement_invoice_transaction_credit.getStopDate())

      self.assertEquals(1.0,
        simulation_movement_invoice_transaction_debit.getQuantity())
      self.assertEquals("unit/piece",
        simulation_movement_invoice_transaction_debit.getQuantityUnit())
      self.assertEquals(1.0,
        simulation_movement_invoice_transaction_debit.getPrice())
      self.assertEquals(None,
        simulation_movement_invoice_transaction_debit.getPriceCurrency())
      self.assertEquals("account_module/receivable",
        simulation_movement_invoice_transaction_debit.getSource())
      self.assertEquals("organisation_module/vifib_internet",
        simulation_movement_invoice_transaction_debit.getSourceSection())
      self.assertEquals("account_module/payable",
        simulation_movement_invoice_transaction_debit.getDestination())
      self.assertEquals("person_module/test_vifib_customer",
        simulation_movement_invoice_transaction_debit.getDestinationSection())
      self.assertEquals("currency_module/EUR",
        simulation_movement_invoice_transaction_debit.getResource())
      self.assertEquals(open_order_line.getSpecialise(),
        simulation_movement_invoice_transaction_debit.getSpecialise())
      self.assertEquals("default/accounting",
        simulation_movement_invoice_transaction_debit.getTradePhase())
      self.assertEquals(expected_time_frame_list[idx+1],
        simulation_movement_invoice_transaction_debit.getStartDate())
      self.assertEquals(expected_time_frame_list[idx+1],
        simulation_movement_invoice_transaction_debit.getStopDate())

      # credit simulation movement has no content
      self.assertEquals([],
        simulation_movement_invoice_transaction_credit.contentValues(
          portal_type="Applied Rule"))

      # fetch payment level simulation
      applied_rule_credit_payment_list = \
        simulation_movement_invoice_transaction_debit.contentValues(
          portal_type="Applied Rule")
      self.assertEquals(1, len(applied_rule_credit_payment_list))
      applied_rule_credit_payment = \
        applied_rule_credit_payment_list[0].getObject()
      self.assertNotEquals(None, applied_rule_credit_payment)
      simulation_movement_credit_payment_list = \
        applied_rule_credit_payment.contentValues(
          portal_type="Simulation Movement")
      self.assertEquals(2, len(simulation_movement_credit_payment_list))
      simulation_movement_credit_payment_credit = None
      simulation_movement_credit_payment_debit = None
      for simulation_movement_credit_payment in \
        simulation_movement_credit_payment_list:
        if "business_process_module/erp5_default_business_process/payment_credit_path" \
          in simulation_movement_credit_payment.getCausalityList():
            simulation_movement_credit_payment_credit = \
              simulation_movement_credit_payment.getObject()
        if "business_process_module/erp5_default_business_process/payment_debit_path" \
          in simulation_movement_credit_payment.getCausalityList():
            simulation_movement_credit_payment_debit = \
              simulation_movement_credit_payment.getObject()
      self.assertNotEquals(None, simulation_movement_credit_payment_credit)
      self.assertNotEquals(None, simulation_movement_credit_payment_debit)

      # check payment level of simulation
      self.assertEquals(-1.0,
        simulation_movement_credit_payment_credit.getQuantity())
      self.assertEquals("unit/piece",
        simulation_movement_credit_payment_credit.getQuantityUnit())
      self.assertEquals(1.0,
        simulation_movement_credit_payment_credit.getPrice())
      self.assertEquals("currency_module/EUR",
        simulation_movement_credit_payment_credit.getResource())
      self.assertEquals("account_module/receivable",
        simulation_movement_credit_payment_credit.getSource())
      self.assertEquals("organisation_module/vifib_internet",
        simulation_movement_credit_payment_credit.getSourceSection())
      self.assertEquals("account_module/payable",
        simulation_movement_credit_payment_credit.getDestination())
      self.assertEquals("person_module/test_vifib_customer",
        simulation_movement_credit_payment_credit.getDestinationSection())
      self.assertEquals(open_order_line.getSpecialise(),
        simulation_movement_credit_payment_credit.getSpecialise())
      self.assertEquals("default/payment",
        simulation_movement_credit_payment_credit.getTradePhase())
      self.assertEquals(expected_time_frame_list[idx+1],
        simulation_movement_credit_payment_credit.getStartDate())
      self.assertEquals(expected_time_frame_list[idx+1],
        simulation_movement_credit_payment_credit.getStopDate())

      self.assertEquals(1.0,
        simulation_movement_credit_payment_debit.getQuantity())
      self.assertEquals("unit/piece",
        simulation_movement_credit_payment_debit.getQuantityUnit())
      self.assertEquals(1.0,
        simulation_movement_credit_payment_debit.getPrice())
      self.assertEquals("currency_module/EUR",
        simulation_movement_credit_payment_debit.getResource())
      self.assertEquals("account_module/bank",
        simulation_movement_credit_payment_debit.getSource())
      self.assertEquals("organisation_module/vifib_internet",
        simulation_movement_credit_payment_debit.getSourceSection())
      self.assertEquals("account_module/bank",
        simulation_movement_credit_payment_debit.getDestination())
      self.assertEquals("person_module/test_vifib_customer",
        simulation_movement_credit_payment_debit.getDestinationSection())
      self.assertEquals(open_order_line.getSpecialise(),
        simulation_movement_credit_payment_debit.getSpecialise())
      self.assertEquals("default/payment",
        simulation_movement_credit_payment_debit.getTradePhase())
      self.assertEquals(expected_time_frame_list[idx+1],
        simulation_movement_credit_payment_debit.getStartDate())
      self.assertEquals(expected_time_frame_list[idx+1],
        simulation_movement_credit_payment_debit.getStopDate())

      # check next simulation movement
      idx += 1

  def test_OpenOrder_request_changeSoftwareType(self):
    """
    Check that requesting the same instance with a different software type
    does not create a new instance
    """
    self.computer_partition_amount = 1
    sequence_list = SequenceList()
    sequence_string = \
        self.prepare_installed_computer_partition_sequence_string + """
      LoginDefaultUser
      CheckSimulationMovement
      Tic
      SlapLogout
    """ + """
      LoginTestVifibCustomer
      RequestSoftwareInstanceStart
      Tic
      Logout
      LoginDefaultUser
      CheckComputerPartitionInstanceHostingSalePackingListConfirmed
      Logout
      SlapLoginCurrentComputer \
      SoftwareInstanceStarted \
      Tic \
      SlapLogout \
      \
      LoginDefaultUser \
      CheckComputerPartitionInstanceHostingSalePackingListStarted \
      Logout \
    """
    sequence_list.addSequenceString(sequence_string)
    sequence_list.play(self)

def test_suite():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(TestVifibOpenOrderSimulation))
  return suite
