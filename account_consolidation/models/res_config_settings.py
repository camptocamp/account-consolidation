# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    consolidation_diff_account_id = fields.Many2one(
        'account.account',
        string='Consolidation difference account',
        related='company_id.consolidation_diff_account_id',
        help=("Conso. differences will be affected"
              " to this account"))

    consolidation_default_journal_id = fields.Many2one(
        'account.journal',
        string='Default consolidation journal',
        related='company_id.consolidation_default_journal_id',
        help="Default journal to generate consolidation entries")

    is_consolidation = fields.Boolean(
        string='Consolidation',
        related='company_id.is_consolidation', readonly=True,
        help='Check this box if you want to consolidate in this company.')
