# -*- coding: utf-8 -*-

from datetime import date

from odoo import fields, models, api, _


class AccountPartnerLedger(models.TransientModel):
    _name = "account.report.partner.ledger"
    _inherit = "account.common.partner.report"
    _description = "Account Partner Ledger"

    result_selection = fields.Selection(selection_add=[], default='customer_supplier')
    amount_currency = fields.Boolean("With Currency",
                                     help="It adds the currency column on "
                                          "report if the currency differs from "
                                          "the company currency.")
    reconciled = fields.Boolean('Reconciled Entries', default=True)
    previous_balance = fields.Boolean('Previous Balance', default=True,
                                      help="Show previous balance before the start date.")
    group_by_account = fields.Boolean(
        'Group by Account', default=True,
        help="Print a separate partner ledger card per account. "
             "When disabled, all accounts of the partner are merged into one card.")
    journal_ids = fields.Many2many(
        default=lambda self: self.env['account.journal'].with_context(active_test=False).search(
            [('company_id', '=', self.company_id.id)]),
    )
    date_from = fields.Date(default=lambda self: date(date.today().year, 1, 1))
    date_to = fields.Date(default=lambda self: date(date.today().year, 12, 31))

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.journal_ids = self.env['account.journal'].with_context(active_test=False).search(
                [('company_id', '=', self.company_id.id)])
        else:
            self.journal_ids = self.env['account.journal'].with_context(active_test=False).search([])

    def _get_report_base_filename(self):
        report = self.env.ref(
            'accounting_pdf_reports.action_report_partnerledger',
            raise_if_not_found=False,
        )
        base = (report.name if report else _('Partner Ledger')).replace(' ', '_')
        if self.partner_ids:
            names = '_'.join(
                name.replace(' ', '_').replace('/', '_').replace('\\', '_')
                for name in self.partner_ids.mapped('name')
            )
            return base + '_' + names
        return base

    def _get_report_data(self, data):
        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled,
                             'amount_currency': self.amount_currency,
                             'previous_balance': self.previous_balance,
                             'group_by_account': self.group_by_account})
        return data

    def _print_report(self, data):
        data = self._get_report_data(data)
        report_filename = self._get_report_base_filename()
        return self.env.ref(
            'accounting_pdf_reports.action_report_partnerledger'
        ).with_context(landscape=True, report_filename=report_filename).report_action(self, data=data)
