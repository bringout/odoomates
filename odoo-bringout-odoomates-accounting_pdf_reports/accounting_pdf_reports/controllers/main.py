# -*- coding: utf-8 -*-

import json

from odoo.http import content_disposition, request, route
from odoo.addons.web.controllers.report import ReportController


class CustomReportController(ReportController):

    @route()
    def report_download(self, data, context=None, token=None):
        response = super().report_download(data, context=context, token=token)

        try:
            requestcontent = json.loads(data)
            url = requestcontent[0]

            if 'report_partnerledger' in url and context:
                ctx = json.loads(context)
                report_filename = ctx.get('report_filename')
                if report_filename:
                    response.headers['Content-Disposition'] = content_disposition(
                        report_filename + '.pdf'
                    )
        except Exception:
            pass

        return response
