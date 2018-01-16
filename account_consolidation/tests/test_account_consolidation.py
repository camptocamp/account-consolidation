# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import TransactionCase


class TestAccountConsolidation(TransactionCase):

    def setUp(self):
        super(TestAccountConsolidation, self).setUp()

        subsidiaries = [('subsidiary_a', 'subA'), ('subsidiary_b', 'subB')]

        opening_entries = {
            'date': '2018-01-01',
            'label': 'Opening',
            'subA': [('ass1', 130), ('lia1', -80), ('lia2', -50)],
            'subB': [('ass1', 170), ('lia1', -160), ('lia2', -10)]
        }

        p1_entries = {
            'date': '2018-01-20',
            'label': 'P1',
            'subA': [
                ('exp1', 20), ('exp2', 30), ('exp3', 65), ('rev1', -50),
                ('rev2', -90), ('ass1', 80), ('lia1', -10), ('lia2', -45)
            ],
            'subB': [
                ('exp1', 15), ('exp2', 26), ('exp3', 12), ('rev1', -88),
                ('rev2', -70), ('ass1', 155), ('lia1', -40), ('lia2', -10)
            ]
        }

        p2_entries = {
            'date': '2018-02-15',
            'label': 'P2',
            'subA': [
                ('exp1', 10), ('exp2', 55), ('exp3', 40), ('rev1', -120),
                ('rev2', -75), ('ass1', 40), ('lia1', 50)
            ],
            'subB': [
                ('exp1', 10), ('exp2', 55), ('exp3', 40), ('rev1', -120),
                ('ass1', 80), ('lia1', -30), ('lia2', -35)]
        }

        entries = [opening_entries, p1_entries, p2_entries]

        for sub in subsidiaries:

            company = self.env.ref('account_consolidation.%s' % sub[0])
            setattr(self, sub[0], company)
            self.env.user.write({
                'company_ids': [(4, company.id, False)]
            })
            self.env.user.company_id = company

            journal = self.env.ref('account_consolidation.%s_op_journal' %
                                   sub[1])
            
            for entry in entries:

                lines_list = []

                for move_tuple in entry[sub[1]]:
                    
                    account = self.env.ref('account_consolidation.%s_%s' %
                                           (sub[1], move_tuple[0]))
                    line_vals = {
                        'name': entry['label'],
                        'account_id': account.id,
                        'company_id': company.id,
                        'debit': 0,
                        'credit': 0
                    }

                    amount = move_tuple[1]
                    if amount > 0:
                        line_vals.update({'debit': amount})
                    elif amount < 0:
                        line_vals.update({'credit': -amount})

                    lines_list.append(line_vals)

                lines_vals = [(0, 0, l) for l in lines_list]
                    
                move_vals = {
                    'journal_id': journal.id,
                    'company_id': company.id,
                    'ref': entry['label'],
                    'date': fields.Date.from_string(entry['date']),
                    'line_ids': lines_vals
                }

                move = self.env['account.move'].create(move_vals)
                # Post only moves of subisdiary B
                if sub[0] == 'subsidiary_b':
                    move.post()

        self.holding = self.env.ref('base.main_company')
        self.env.user.company_id = self.holding

    def test_default_values(self):
        wizard = self.env['account.consolidation.consolidate'].create({
            'date_from': fields.Date.from_string('2018-01-01'),
            'date_to': fields.Date.from_string('2018-01-31'),
        })
        self.assertEqual(wizard.company_id, self.holding)
        self.assertEqual(wizard.journal_id,
                         self.holding.consolidation_default_journal_id)
        self.assertEqual(wizard.subsidiary_ids,
                         self.subsidiary_a | self.subsidiary_b)
        self.assertEqual(wizard.target_move, 'posted')

    def test_consolidation_checks_ok(self):
        wizard = self.env['account.consolidation.check'].create({})
        wizard.check_account_mapping()
        self.assertEqual(wizard.state, 'ok')
        self.assertEqual(wizard.message, '<h2>Checks ok !</h2>')

    def test_consolidation_checks_error(self):
        self.env.ref('account_consolidation.subA_exp1').write({
            'consolidation_account_id': False
        })
        wizard = self.env['account.consolidation.check'].create({})
        wizard.check_account_mapping()
        self.assertEqual(wizard.state, 'error')

    def test_consolidation_31_jan_all(self):
        wizard = self.env['account.consolidation.consolidate'].create({
            'date_from': fields.Date.from_string('2018-01-01'),
            'date_to': fields.Date.from_string('2018-01-31'),
            'target_move': 'all'
        })
        res = wizard.run_consolidation()
        move_ids = res['domain'][0][2]
        conso_moves = self.env['account.move'].browse(move_ids)

        conso_results = {
            'subA': {
                'exp1': 20, 'exp2': 30, 'exp3': 65, 'rev1': -50,
                'rev2': -90, 'ass1': 210, 'lia1': -90, 'lia2': -95
            },
            'subB': {
                'exp1': 15, 'exp2': 26, 'exp3': 12, 'rev1': -88,
                'rev2': -70, 'ass1': 325, 'lia1': -200, 'lia2': -20, 'ced': 0
            }
        }

        for move in conso_moves:

            for line in move.line_ids:

                if line.consol_company_id == self.subsidiary_a:
                    conso_comp = 'subA'
                    currency_diff = False
                elif line.consol_company_id == self.subsidiary_b:
                    conso_comp = 'subB'
                    currency_diff = True

                acc = line.account_id.code.lower()

                if currency_diff:
                    self.assertEqual(line.amount_currency,
                                     conso_results[conso_comp][acc])
                else:
                    self.assertEqual(line.balance,
                                     conso_results[conso_comp][acc])

    def test_consolidation_28_feb_posted(self):
        wizard = self.env['account.consolidation.consolidate'].create({
            'date_from': fields.Date.from_string('2018-01-01'),
            'date_to': fields.Date.from_string('2018-02-28'),
        })
        res = wizard.run_consolidation()
        move_ids = res['domain'][0][2]
        conso_moves = self.env['account.move'].browse(move_ids)

        conso_results = {
            'exp1': 25, 'exp2': 81, 'exp3': 52, 'rev1': -208,
            'rev2': -70, 'ass1': 405, 'lia1': -230, 'lia2': -55, 'ced': 0
        }

        for move in conso_moves:

            for line in move.line_ids:

                self.assertEqual(line.consol_company_id, self.subsidiary_b)

                acc = line.account_id.code.lower()

                self.assertEqual(line.amount_currency, conso_results[acc])

    def test_consolidation_31_jan_with_exchange_rates(self):
        wizard = self.env['account.consolidation.consolidate'].create({
            'date_from': fields.Date.from_string('2018-01-01'),
            'date_to': fields.Date.from_string('2018-01-31'),
        })
        res = wizard.run_consolidation()
        move_ids = res['domain'][0][2]
        conso_moves = self.env['account.move'].browse(move_ids)

        conso_results = {
            # monthly rate used : 1.3
            'exp1': 11.54, 'exp2': 20, 'exp3': 9.23, 'rev1': -67.69,
            'rev2': -53.85,
            # spot rate used : 1.36
            'ass1': 238.97, 'lia1': -147.06, 'lia2': -14.71,
            'ced': 3.57
        }
        for move in conso_moves:

            for line in move.line_ids:

                self.assertEqual(line.consol_company_id, self.subsidiary_b)

                acc = line.account_id.code.lower()

                self.assertEqual(line.balance, conso_results[acc])
