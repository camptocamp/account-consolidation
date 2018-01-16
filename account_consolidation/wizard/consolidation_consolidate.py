# Copyright 2011-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError


class AccountConsolidationConsolidate(models.TransientModel):
    _name = 'account.consolidation.consolidate'
    _inherit = 'account.consolidation.base'

    def _default_journal(self):
        return self._default_company().consolidation_default_journal_id

    date_from = fields.Date(required=True)

    date_to = fields.Date(required=True)

    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        default=lambda self: self._default_journal(),
        required=True)

    target_move = fields.Selection(
        [('posted', 'All Posted Entries'),
         ('all', 'All Entries')],
        string='Target Moves',
        default='posted',
        required=True)

    subsidiary_ids = fields.Many2many(
        'res.company',
        'account_conso_conso_comp_rel',
        'conso_id',
        'company_id',
        domain=[('consolidation_percentage', '>', 0)],
        string='Subsidiaries',
        required=True)

    def _prepare_rate_difference_line(self, move_lines_list):
        """
        Prepares a move line to balance the move to be created, as the move
        lines can be unbalanced if different currencies are used

        :param move_lines_list: List of move lines to generate
        :return: Dictionnary to create exchange difference move line
        """

        if not move_lines_list:
            return False
        diff_account = self.company_id.consolidation_diff_account_id
        if not diff_account:
            raise UserError(_('Please set the Consolidation difference '
                              'account for company %s in accounting settings.')
                            % self.company_id.name)

        debit = credit = 0.0

        for line_vals in move_lines_list:
            debit += line_vals.get('debit')
            credit += line_vals.get('credit')

        balance = debit - credit

        # We do not want to create counter parts for amount smaller than
        # "holding" company currency rounding policy.
        # As generated lines are in draft state, accountant will be able to
        # manage special cases
        move_is_balanced = self.company_id.currency_id.is_zero(balance)
        if move_is_balanced:
            return False
        else:
            return {
                'account_id': diff_account.id,
                'debit': abs(balance) if balance < 0.0 else 0.0,
                'credit': balance if balance > 0.0 else 0.0,
                'name': _('Consolidation difference (%s - %s)') % (
                    self.date_from, self.date_to
                )
            }

    def get_account_balance(self, account):
        """
        Gets the accounting balance for the specified account according to
        Wizard settings

        :param account: Recordset of the account

        :return: Balance of the account
        """
        move_lines = self.env['account.move.line'].search(
            [('company_id', '=', account.company_id.id),
             ('account_id', '=', account.id),
             ('date', '>=', self.date_from),
             ('date', '<=', self.date_to)])
        if self.target_move == 'posted':
            move_lines = move_lines.filtered(lambda l:
                                             l.move_id.state == 'posted')
        return sum([l.balance for l in move_lines])

    def _prepare_consolidate_account(self, holding_account, subsidiary):
        """
        Consolidates the subsidiary accounts on the holding account
        Prepare a dictionnary for each move lines to generate

        :param holding_account: Recordset of the account to consolidate
                                (on the holding), the method will
                                find the subsidiary's corresponding accounts
        :param subsidiary: Recordset of the subsidiary to consolidate

        :return: Dictionnary to create move lines
        """

        account_obj = self.env['account.account']

        subs_accounts = account_obj.search(
            [('company_id', '=', subsidiary.id),
             ('consolidation_account_id', '=', holding_account.id)])

        if not subs_accounts:
            # an account may exist on the holding and not be used as
            # consolidation account in the subsidiaries,
            # nothing to do
            return False

        vals = {
            'name': _("Consolidation (%s - %s)") % (self.date_from,
                                                    self.date_to),
            'account_id': holding_account.id
        }

        for account in subs_accounts:
            balance = self.get_account_balance(account)
            if not balance:
                return False

            conso_percentage = subsidiary.consolidation_percentage / 100
            conso_balance = balance * conso_percentage

            holding_account_currency = (
                    holding_account.currency_id or
                    holding_account.company_id.currency_id)
            account_currency = (
                    account.currency_id or account.company_id.currency_id)

            # If holding and subsidiary account are in the same currency
            # We can use the subsidiary account balance without conversion
            if holding_account_currency == account_currency:
                vals.update({
                    'debit': conso_balance if conso_balance > 0.0 else 0.0,
                    'credit':
                        abs(conso_balance) if conso_balance < 0.0 else 0.0,
                })
            else:
                # If holding and subsidiary account are in different currencies
                # we use monthly rate for P&L accounts and spot rate for
                # Balance sheet accounts
                if not holding_account.user_type_id.include_initial_balance:
                    account_currency = account_currency.with_context(
                        monthly_rate=True)
                    rate_text = _('monthly rate : %s') % (
                        account_currency.with_context(
                            date=self.date_to).monthly_rate)
                else:
                    rate_text = _('spot rate : %s') % (
                        account_currency.with_context(
                            date=self.date_to).rate)

                currency_value = account_currency.with_context(
                    date=self.date_to).compute(conso_balance,
                                               holding_account_currency)

                vals.update({
                    'currency_id': account_currency.id,
                    'amount_currency': conso_balance,
                    'debit': currency_value if currency_value > 0.0 else 0.0,
                    'credit': abs(
                        currency_value) if currency_value < 0.0 else 0.0,
                    'name': '%s - %s' % (vals['name'], rate_text)
                })

        return vals

    def consolidate_subsidiary(self, subsidiary):
        """
        Consolidate one subsidiary on the Holding.
        Create a move per subsidiary and a move line per account

        :param subsidiary: Recordset of the subsidiary to consolidate
                           on the holding

        :return: Recordset of the created move
        """
        holding_accounts = self.env['account.account'].search(
            [('company_id', '=', self.company_id.id)])

        move_vals = {
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'consol_company_id': subsidiary.id,
            'ref': _('Consolidation'),
            'date': self.date_to
        }

        move_lines_to_generate = []
        # prepare a move line per account
        for account in holding_accounts:
            move_line_vals = self._prepare_consolidate_account(account,
                                                               subsidiary)
            if move_line_vals:
                move_line_vals.update({
                    'journal_id': self.journal_id.id,
                    'company_id': self.company_id.id,
                    'date': self.date_to,
                })
                move_lines_to_generate.append(move_line_vals)

        # prepare a rate difference move line
        if move_lines_to_generate:
            move_line_vals = self._prepare_rate_difference_line(
                move_lines_to_generate)
            if move_line_vals:
                move_line_vals.update({
                    'journal_id': self.journal_id.id,
                    'company_id': self.company_id.id,
                    'date': self.date_to,
                })
                move_lines_to_generate.append(move_line_vals)

            # Create the move with all the move lines
            move_vals.update({'line_ids': [
                (0, False, vals) for vals in move_lines_to_generate]})
            return self.env['account.move'].create(move_vals)
        else:
            # Return an empty recordset if there is no move to generate
            return self.env['account.move']

    def run_consolidation(self):
        """
        Consolidate all selected subsidiaries onto the Holding accounts

        :return: dict to open an Entries view filtered on the created moves
        """
        super(AccountConsolidationConsolidate, self).run_consolidation()

        created_moves = self.env['account.move']

        for subsidiary in self.subsidiary_ids.filtered(
                lambda s: s.consolidation_percentage > 0):
            created_moves |= self.consolidate_subsidiary(subsidiary)

        if created_moves:
            return {
                'name': _('Consolidation Moves'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'domain': [('id', 'in', created_moves.ids)],
            }
        else:
            raise ValidationError(
                _('Could not generate any consolidation entries.'))
