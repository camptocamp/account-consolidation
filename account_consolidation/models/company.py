# Copyright 2011-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _default_consolidation_percentage(self):
        return 100

    consolidation_diff_account_id = fields.Many2one(
        'account.account',
        string='Consolidation difference account',
        # domain=[('type', '=', 'other')],
        help=("Conso. differences will be affected"
              " to this account"))

    consolidation_default_journal_id = fields.Many2one(
        'account.journal',
        string='Default consolidation journal',
        help="Default journal to generate consolidation entries")

    is_consolidation = fields.Boolean(
        string='Consolidation',
        help='Check this box if you want to consolidate in this company.'
    )

    consolidation_percentage = fields.Float(
        string='Consolidation percentage',
        help='Define a percentage to consolidate this company (in percents)',
        default=lambda self: self._default_consolidation_percentage(),
    )

    @api.constrains('consolidation_percentage')
    def _check_consolidation_percentage(self):
        for company in self:
            if company.consolidation_percentage and company.is_consolidation:
                raise ValidationError(_(
                    'Consolidation percentage can only be defined on '
                    'subsidiaries to consolidate, and not on consolidation '
                    'company.'))
            if (
                    company.consolidation_percentage < 0 or
                    company.consolidation_percentage > 100
            ):
                raise ValidationError(_(
                    'Consolidation percentage can only be defined in the range'
                    'between 0 and 100.'
                ))
