from test_suite import SavedTestSuite, ProjectTestSuite

slapos_bt_list = [
    'erp5_web_shacache',
    'erp5_web_shadir',
    'slapos_accounting',
    'slapos_cache',
    'slapos_cloud',
    'slapos_erp5',
    'slapos_pdm',
    'slapos_rest_api',
    'slapos_slap_tool',
    'slapos_web',
  ]

class VIFIB(SavedTestSuite, ProjectTestSuite):
  _product_list = ['Vifib']
  _saved_test_id = 'Products.Vifib.tests.VifibMixin.testVifibMixin'
  _bt_list = slapos_bt_list + [
    'vifib_base',
    'vifib_data',
    'vifib_erp5',
    'vifib_slap',
    'vifib_upgrader',
  ]

class SlapOSCloud(SavedTestSuite, ProjectTestSuite):
  _product_list = ['SlapOS']
  _saved_test_id = 'Products.SlapOS.tests.testSlapOSMixin.testSlapOSMixin'
  _bt_list = slapos_bt_list
