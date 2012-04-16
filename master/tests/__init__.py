from test_suite import SavedTestSuite, ProjectTestSuite

class SLAPOS_MASTER(SavedTestSuite, ProjectTestSuite):
  _bt_list = [
#     'vifib_slapos_core',
#     'vifib_slapos_master',
  ]
  _product_list = ['Vifib']
  _saved_test_id = 'Products.Vifib.tests.VifibMixin'

class VIFIB(SLAPOS_MASTER):
  _bt_list = SLAPOS_MASTER._bt_list + [
    'vifib_base',
    'vifib_core',
    'vifib_crm',
    'vifib_data',
    'vifib_data_category',
    'vifib_data_web',
    'vifib_erp5',
    'vifib_forge_release',
    'vifib_l10n_fr',
    'vifib_mysql_innodb_catalog',
    'vifib_open_trade',
    'vifib_slap',
    'vifib_software_pdm',
    'vifib_upgrader',
    'vifib_web',
  ]
