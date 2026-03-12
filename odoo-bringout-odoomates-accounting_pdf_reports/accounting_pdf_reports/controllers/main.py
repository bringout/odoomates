# -*- coding: utf-8 -*-

import json
import logging

from werkzeug.urls import url_parse

from odoo import http
from odoo.http import content_disposition, request
from odoo.tools.safe_eval import safe_eval, time
from odoo.addons.web.controllers.report import ReportController

_logger = logging.getLogger(__name__)


class ReportControllerExt(ReportController):

    @http.route(['/report/download'], type='http', auth="user")
    def report_download(self, data, context=None, token=None):
        response = super().report_download(data, context=context, token=token)

        # Fix filename for data-driven wizard reports where active_ids
        # are passed in context (not in URL path), so print_report_name
        # is not evaluated by the standard controller.
        try:
            requestcontent = json.loads(data)
            url, type_ = requestcontent[0], requestcontent[1]

            if type_ in ['qweb-pdf', 'qweb-text']:
                extension = 'pdf' if type_ == 'qweb-pdf' else 'txt'
                pattern = '/report/pdf/' if type_ == 'qweb-pdf' else '/report/text/'
                reportname = url.split(pattern)[1].split('?')[0]

                if '/' not in reportname:
                    # Data-driven report (no docids in URL path).
                    # Extract active_ids from the URL context parameter.
                    ctx = {}
                    query = url_parse(url).decode_query(cls=dict)
                    if 'context' in query:
                        ctx.update(json.loads(query['context']))

                    active_ids = ctx.get('active_ids', [])
                    if active_ids and len(active_ids) == 1:
                        report = request.env['ir.actions.report']._get_report_from_name(reportname)
                        if report and report.print_report_name:
                            obj = request.env[report.model].browse(active_ids[0])
                            if obj.exists():
                                report_name = safe_eval(
                                    report.print_report_name,
                                    {'object': obj, 'time': time},
                                )
                                filename = "%s.%s" % (report_name, extension)
                                response.headers.set(
                                    'Content-Disposition',
                                    content_disposition(filename),
                                )
        except Exception:
            pass  # Keep whatever filename super() set

        return response
