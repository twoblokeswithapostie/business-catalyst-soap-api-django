=====================
Django app for connecting to Business Catalyst SOAP API 
=====================

This application can be embedded into a Django project and be used to sync data between Business Catalyst and Django project.
It has almost every SOAP web service implemented, and models for almost all things in Business Catalyst. 

Quick start guide:
------------------

Installation:
*************

1. Download and paste into your project

2. Add ``bc_api`` to your project's list of INSTALLED_APPS

3. Install requirements : suds-jurko, pytz

3. Migrate your database

Usage:
*********

To use the API simply initialise the wrapper with the BCSite object and use it's method. Example:

```
def get_last_days_orders():
    bc_site = BCSite.objects.get(site_code="MY_SITE")
    crm_wrapper = CrmWrapper(bc_site)
    crm_wrapper.get_or_update_orders(datetime.datetime.now()-datetime.timedelta(days=1))
```
