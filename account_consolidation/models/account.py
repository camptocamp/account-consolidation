# Copyright 2011-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    is_consolidation = fields.Boolean(
        string='Is consolidation', related='company_id.is_consolidation',
        help='Mark this to use this account as a consolidation account'
    )

    consolidation_account_id = fields.Many2one(
        'account.account',
        string='Consolidation account',
        domain=[('is_consolidation', '=', True)],
        help='Consolidation moves will be generated on this account'
    )

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        if self.env.user.has_group(
                'account_consolidation.consolidation_manager'):
            result = []
            for account in self:
                if account.company_id != self.env.user.company_id:
                    name = '%s %s (%s)' % (account.code, account.name,
                                           account.company_id.name)
                else:
                    name = account.code + ' ' + account.name
                result.append((account.id, name))
        else:
            result = super(AccountAccount, self).name_get()
        return result
