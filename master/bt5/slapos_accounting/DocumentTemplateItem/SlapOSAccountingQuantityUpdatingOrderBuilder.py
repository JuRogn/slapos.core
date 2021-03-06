from Products.ERP5.Document.OrderBuilder import OrderBuilder
from Products.ERP5.Document.SimulatedDeliveryBuilder import BUILDING_KEY
from Products.ERP5Type.TransactionalVariable import getTransactionalVariable
from Products.ERP5.mixin.builder import BuilderMixin

class SlapOSAccountingQuantityUpdatingOrderBuilder(OrderBuilder):
  def _setDeliveryMovementProperties(self, delivery_movement,
                                     simulation_movement, property_dict,
                                     update_existing_movement=0,
                                     force_update=0, activate_kw=None):
    """
      Initialize or update delivery movement properties.
      Set delivery ratio on simulation movement.
      Create the relation between simulation movement
      and delivery movement.
    """
    delivery = delivery_movement.getExplanationValue()
    building = getTransactionalVariable()[BUILDING_KEY]
    if delivery in building:
      building.add(delivery_movement)
    simulation_movement.recursiveReindexObject(activate_kw=dict(
      activate_kw or (), tag='built:'+delivery.getPath()))
    BuilderMixin._setDeliveryMovementProperties(
                            self, delivery_movement,
                            simulation_movement, property_dict,
                            update_existing_movement=update_existing_movement,
                            force_update=force_update, 
                            activate_kw=activate_kw)

    if update_existing_movement and not force_update:
      delivery_movement.edit(
          quantity=delivery_movement.getQuantity() +
              simulation_movement.getQuantity())
    else:
      simulation_movement._setDeliveryRatio(1)
    delivery_movement = delivery_movement.getRelativeUrl()
    if simulation_movement.getDeliveryList() != [delivery_movement]:
      simulation_movement._setDelivery(delivery_movement)
      if not simulation_movement.isTempDocument():
        try:
          getCausalityState = delivery.aq_explicit.getCausalityState
        except AttributeError:
          return
        if getCausalityState() == 'building':
          # Make sure no other node is changing state of the delivery
          delivery.serializeCausalityState()
        else:
          delivery.startBuilding()
