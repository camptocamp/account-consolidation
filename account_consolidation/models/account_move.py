# Copyright 2011-2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from lxml import etree

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    consol_company_id = fields.Many2one(
        'res.company',
        'Consolidated from Company',
        readonly=True)

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                         submenu=False):
        """ Override to set the column consol_company_id invisible in the
            embedded account.move.line tree view, if the user is not connected
            to a consolidation company."""
        res = super(AccountMove, self)._fields_view_get(
            view_id, view_type, toolbar, submenu
        )
        if view_type == 'form':
            xml = etree.fromstring(res['arch'])
            node = xml.find(".//tree//field[@name='consol_company_id']")
            if node is not None:
                node.set('attrs', str({
                    'column_invisible':
                        not self.env.user.company_id.is_consolidation
                }))
                res['arch'] = etree.tostring(xml)
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    consol_company_id = fields.Many2one(
        'res.company',
        related='move_id.consol_company_id',
        string='Consolidated from',
        store=True,  # for the group_by
        readonly=True)

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                         submenu=False):
        """ Override to set the column consol_company_id invisible in the
            account.move.line tree view, if the user is not connected
            to a consolidation company."""
        res = super(AccountMoveLine, self)._fields_view_get(
            view_id, view_type, toolbar, submenu
        )

        if view_id == self.env.ref('account.view_move_line_tree').id:
            xml = etree.fromstring(res['arch'])
            node = xml.find(".//field[@name='consol_company_id']")
            if node is not None:
                node.set('attrs', str({
                    'column_invisible':
                        not self.env.user.company_id.is_consolidation
                }))
            res['arch'] = etree.tostring(xml)

        return res
