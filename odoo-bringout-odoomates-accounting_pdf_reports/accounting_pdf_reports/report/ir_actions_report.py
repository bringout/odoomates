# -*- coding: utf-8 -*-
from odoo import models

# Kartica partnera (Partner Ledger). When run WITHOUT the HTML header
# (use_header=False, the default) the body uses web.basic_layout, so Odoo passes
# wkhtmltopdf no --header-html/--footer-html and the report survives huge runs
# (all partners = 600+ pages would otherwise crash wkhtmltopdf 0.12.6 with -11,
# because the per-page HTML header re-loads the full report CSS bundle on every
# page). Page numbers are still required, so we add wkhtmltopdf's NATIVE footer
# (rendered by wkhtmltopdf itself, not as an HTML overlay → no crash).
# See profile/radix/docs/CASE_KARTICA_PARTNERA_MEMORY_ERROR.md.
PARTNER_LEDGER_REPORT = 'accounting_pdf_reports.report_partnerledger'


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _is_partner_ledger(self, report_ref):
        if self and getattr(self, 'report_name', None) == PARTNER_LEDGER_REPORT:
            return True
        return isinstance(report_ref, str) and report_ref == PARTNER_LEDGER_REPORT

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        form = (data or {}).get('form') or {}
        if not form.get('use_header') and self._is_partner_ledger(report_ref):
            self = self.with_context(partnerledger_native_footer=True)
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

    def _build_wkhtmltopdf_args(self, paperformat_id, landscape,
                               specific_paperformat_args=None, set_viewport_size=False):
        args = super()._build_wkhtmltopdf_args(
            paperformat_id, landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size)
        if self.env.context.get('partnerledger_native_footer'):
            args += ['--footer-center', 'Strana [page] / [topage]',
                     '--footer-font-size', '7', '--footer-spacing', '3']
        return args
