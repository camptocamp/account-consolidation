.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=====================
Account Consolidation
=====================

This module extends the functionality of accounting to allow you to consolidate
journal items in a parent company.

Installation
============

To install this module, you need the module `currency_monthly_rate` to be
available in your system.

Configuration
=============

To configure this module, you need to flag a company as Consolidation on its
form view.

Then in Settings > General settings, you should define a consolidation
difference account and a consolidation journal.

Afterwards, for each subcompany you want to consolidate, you should define a
consolidation account from your consolidation company, on every active account.

You can then use the 'Consolidation : Checks' wizard in Accounting > Adviser to
ensure every active account of your subcompany is set.

Make sure you also defined currency rates and monthly currency rates on the
currencies used in your subcompanies, as P&L accounts are consolidated using
monthly rates and B.S accounts using standard 'spot' rates.

Usage
=====

To consolidate subcompanies in your consolidation company, you should use
'Consolidation : consolidate' wizard in Accounting > Adviser.

You have to select the subcompanies and define period with a date from and a
date to, and select if you want to consolidate all the moves or only posted
ones on that period.

This will generate a journal entry in your consolidation company for each
subcompany.

The generated journal entry is unposted, allowing you to modify or delete it to
run the consolidation again.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/90/11.0

Known issues / Roadmap
======================

* TODO

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-consolidation/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://odoo-community.org/logo.png>`_.

Contributors
------------

* Guewen Baconnier <guewen.baconnier@camptocamp.com>
* Nicolas Bessi
* Vincent Renaville <vincent.renaville@camptocamp.com>
* Akim Juillerat <akim.juillerat@camptocamp.com>

Do not contact contributors directly about support or help with technical issues.

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
