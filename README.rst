=============
ckanext-apis
=============

This extension adds support for representing API type datasets (or *apisets*) in CKAN. 


------------
Requirements
------------

CKAN 2.8.2, ckanext-scheming, ckanext-fluent


------------
Installation
------------

To install ckanext-apis:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-apis Python package into your virtual environment::

     pip install -e git+https://github.com/vrk-kpa/ckanext-apis.git#egg=ckanext-apis

3. Add ``apis`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


---------------
Config Settings
---------------

None


------------------------
Development Installation
------------------------

To install ckanext-apis for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/vrk-kpa/ckanext-apis.git
    cd ckanext-apis
    python setup.py develop
    pip install -r dev-requirements.txt


-----------------
Running the Tests
-----------------

To run the tests, do::

    nosetests --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (``pip install coverage``) then run::

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.apis --cover-inclusive --cover-erase --cover-tests


----------------------------------------
Copying and License
----------------------------------------

This material is copyright (c) 2019 Digital and Population Data Services Agency, Finland.

ckanext-apis is licensed under the GNU Affero General Public License (AGPL) v3.0
