# Copyright 2011-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, _, api
from odoo.exceptions import UserError


class AccountConsolidationBase(models.AbstractModel):
    _name = 'account.consolidation.base'
    _description = 'Common consolidation wizard. Intended to be inherited'

    @api.model
    def _default_company(self):
        return self.env['res.company']._company_default_get()

    @api.model
    def _default_subsidiaries(self):
        return self._default_company().child_ids.filtered(
            lambda c: c.consolidation_percentage > 0)

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self._default_company(),
        domain=[('is_consolidation', '=', True)],
        string='Company',
        required=True)

    subsidiary_ids = fields.Many2many(
        'res.company',
        'account_conso_comp_rel',
        'conso_id',
        'company_id',
        default=lambda self: self._default_subsidiaries(),
        domain=[('consolidation_percentage', '>', 0)],
        string='Subsidiaries',
        required=True)

    def check_subsidiary_mapping(self, conso_holding_accounts, subsidiary):
        """
        Check a Holding Chart of Accounts vs a Subsidiary Virtual
        Chart of Accounts
        All the accounts of the Virtual CoA must exist in the Holding CoA.
        The Holding's CoA may hold accounts which do not exist
        in the Subsidiary's Virtual CoA.

        :param conso_holding_accounts: ID of the Chart of Account of the
                                       holding company
        :param subsidiary: ID of the Chart of Account of the subsidiary
                           company to check

        :return: List of accounts existing on subsidiary but no on holding COA
        """
        subsidiary_accounts = self.env['account.account'].search([
            ('company_id', '=', subsidiary.id),
            ('is_consolidation', '=', False)])

        mapping_errors = {}

        for account in subsidiary_accounts:
            account_errors = []
            if not account.consolidation_account_id:
                account_errors.append(_(
                    'No consolidation account defined for this account'))
                mapping_errors.update({account: account_errors})
                continue

            conso_acc = account.consolidation_account_id

            if conso_acc not in conso_holding_accounts:
                if conso_acc.company_id != self.company_id:
                    account_errors.append(_(
                        'The consolidation account defined for this account '
                        'should be on company %s.') % self.company_id.name)
                if not conso_acc.is_consolidation:
                    account_errors.append(_(
                        'The consolidation account defined for this account '
                        'should be marked as consolidation account.'
                    ))

                mapping_errors.update({account: account_errors})

        return mapping_errors

    def check_account_mapping(self):
        """
        Check the accounts mapping of the subsidiaries vs accounts of the
        holding
        """
        self.ensure_one()

        invalid_items_per_company = {}

        conso_holding_accounts = self.env['account.account'].search([
            ('company_id', '=', self.company_id.id)])

        for subsidiary in self.subsidiary_ids:

            invalid_items = self.check_subsidiary_mapping(
                conso_holding_accounts, subsidiary)

            if any(invalid_items):
                invalid_items_per_company[subsidiary] = invalid_items

        return invalid_items_per_company

    @api.multi
    def run_consolidation(self):
        """
        Proceed with all checks before launch any consolidation step
        This is a base method intended to be inherited with the next
        consolidation steps
        """
        self.ensure_one()

        if self.check_account_mapping():
            raise UserError(
                _('Invalid accounts mappings, please launch the '
                  '"Consolidation: Checks" wizard'))

        # inherit to add the next steps of the reconciliation

        return {'type': 'ir.actions.act_window_close'}
