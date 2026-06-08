# -*- coding: utf-8 -*-
from odoo import models, fields

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

    def _prepare_html(self, html, report_model=False):
        bodies, res_ids, header, footer, args = super()._prepare_html(
            html, report_model=report_model)
        # Header-less mode: drop the web.report_layout header/footer that
        # html_container injects for EVERY layout (incl. basic_layout). That
        # per-page header re-renders the full report CSS bundle and is what
        # crashes wkhtmltopdf -11 on huge runs. Page numbers are restored by the
        # native --footer-center added in _build_wkhtmltopdf_args.
        if self.env.context.get('partnerledger_native_footer'):
            header, footer = '', ''
        return bodies, res_ids, header, footer, args

    def _build_wkhtmltopdf_args(self, paperformat_id, landscape,
                               specific_paperformat_args=None, set_viewport_size=False):
        args = super()._build_wkhtmltopdf_args(
            paperformat_id, landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size)
        if self.env.context.get('partnerledger_native_footer'):
            # Header-less mode: there is no per-page header to reserve space for,
            # so reclaim the paperformat's large top margin (content starts near
            # the top) and shrink the whole render ~15% (zoom) so more rows fit
            # per page — the table still reflows to full width. Both apply ONLY
            # here; the full-header mode (use_header=True) keeps its sizing.
            out, i = [], 0
            while i < len(args):
                a = args[i]
                if a == '--margin-top' and i + 1 < len(args):
                    out += ['--margin-top', '6']
                    i += 2
                    continue
                if a == '--zoom' and i + 1 < len(args):
                    try:
                        zoom = float(args[i + 1]) * 0.85
                    except (TypeError, ValueError):
                        zoom = 0.9
                    out += ['--zoom', '%.4f' % zoom]
                    i += 2
                    continue
                out.append(a)
                i += 1
            # Native footer: page numbers centered, local print date/time on the
            # right (wkhtmltopdf's [date]/[time] use the system locale, so format
            # it ourselves in the user's timezone as DD.MM.YYYY HH:MM).
            stamp = fields.Datetime.context_timestamp(
                self, fields.Datetime.now()).strftime('%d.%m.%Y %H:%M')
            args = out + ['--footer-center', 'Strana [page] / [topage]',
                          '--footer-right', stamp,
                          '--footer-font-size', '7', '--footer-spacing', '3']
        return args
