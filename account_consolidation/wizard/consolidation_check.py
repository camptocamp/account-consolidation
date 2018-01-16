# Copyright 2011-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountConsolidationCheck(models.TransientModel):
    _name = 'account.consolidation.check'
    _inherit = 'account.consolidation.base'
    _description = 'Consolidation Checks. Model used for views'

    message = fields.Html(readonly=True)

    state = fields.Selection([('open', 'Open'), ('error', 'Error'),
                              ('ok', 'Checks ok')], default='open')

    @api.onchange('company_id')
    def onchange_company_id(self):
        self.subsidiary_ids = False

    def check_account_mapping(self):
        """
        Action launched with the button on the view.
        Check the account mapping and display a report of the errors
        """
        invalid_items_per_company = super(AccountConsolidationCheck,
                                          self).check_account_mapping()

        err_lines = []
        for company, account_errors in invalid_items_per_company.items():
            err_lines.append(_("<ul><li>Company : %s</li><ul>") % company.name)
            for account, error in account_errors.items():
                err_lines.append("<li>%s (%s) : %s</li>" % (
                    account.code, account.name, ', '.join(error)))
            err_lines.append('</ul></ul>')
        if err_lines:
            self.message = _('<h2>Invalid account mapping<h2>') + ''.join(err_lines)
            self.state = 'error'
        else:
            self.message = _('<h2>Checks ok !</h2>')
            self.state = 'ok'
        return {
            "type": "ir.actions.do_nothing",
        }
