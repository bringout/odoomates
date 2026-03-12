# Report PDF Filename Override for Data-Driven Wizard Reports

## Problem

In Odoo 16, the `print_report_name` field on `ir.actions.report` is designed to control the PDF download filename. It contains a Python expression (e.g., `object._get_report_base_filename()`) that is evaluated with the report's record as `object`.

However, **for data-driven wizard reports** (reports launched from a wizard that passes `data` to `report_action`), the `print_report_name` expression is **never evaluated** by the standard Odoo 16 report download controller.

### Root Cause: JavaScript URL Construction

In `web/static/src/webclient/actions/action_service.js`, the `_getReportUrl` function constructs the download URL differently based on whether `action.data` is present:

```javascript
function _getReportUrl(action, type) {
    let url = `/report/${type}/${action.report_name}`;
    const actionContext = action.context || {};
    if (action.data && JSON.stringify(action.data) !== "{}") {
        // Data-driven reports: active_ids NOT included in URL path
        const options = encodeURIComponent(JSON.stringify(action.data));
        const context = encodeURIComponent(JSON.stringify(actionContext));
        url += `?options=${options}&context=${context}`;
    } else {
        // Record-based reports: active_ids included in URL path
        if (actionContext.active_ids) {
            url += `/${actionContext.active_ids.join(",")}`;
        }
    }
    return url;
}
```

When `action.data` is present (all wizard-based reports), the URL becomes:
```
/report/pdf/module.report_name?options={...}&context={...}
```

When `action.data` is absent (record-based reports like invoices), the URL becomes:
```
/report/pdf/module.report_name/record_id1,record_id2
```

### Controller Filename Logic

In `web/controllers/report.py`, the `report_download` method:

```python
reportname = url.split(pattern)[1].split('?')[0]

docids = None
if '/' in reportname:
    reportname, docids = reportname.split('/')

# Default filename from report name (translatable field)
report = request.env['ir.actions.report']._get_report_from_name(reportname)
filename = "%s.%s" % (report.name, extension)

# print_report_name ONLY evaluated when docids exist
if docids:
    ids = [int(x) for x in docids.split(",") if x.isdigit()]
    obj = request.env[report.model].browse(ids)
    if report.print_report_name and not len(obj) > 1:
        report_name = safe_eval(report.print_report_name, {'object': obj, 'time': time})
        filename = "%s.%s" % (report_name, extension)
```

Since data-driven reports have no `docids` in the URL path, `print_report_name` is **never evaluated**. The filename defaults to `report.name` (the translatable `name` field of `ir.actions.report`).

### Impact

All wizard-based reports in Odoo 16 that use `print_report_name` are affected:
- Partner Ledger
- General Ledger
- Trial Balance
- Any custom wizard report

The PDF filename always defaults to the report's `name` field translation (e.g., "Kartica partnera.pdf") instead of the custom expression result.

## Solution: Controller Override

### File: `controllers/main.py`

The module overrides the `report_download` controller to handle data-driven reports:

```python
class ReportControllerExt(ReportController):

    @http.route(['/report/download'], type='http', auth="user")
    def report_download(self, data, context=None, token=None):
        response = super().report_download(data, context=context, token=token)

        try:
            requestcontent = json.loads(data)
            url, type_ = requestcontent[0], requestcontent[1]

            if type_ in ['qweb-pdf', 'qweb-text']:
                extension = 'pdf' if type_ == 'qweb-pdf' else 'txt'
                pattern = '/report/pdf/' if type_ == 'qweb-pdf' else '/report/text/'
                reportname = url.split(pattern)[1].split('?')[0]

                if '/' not in reportname:
                    # Data-driven report: extract active_ids from URL context
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
```

### How It Works

1. Calls `super().report_download()` to generate the PDF response normally
2. Detects data-driven reports by checking if `docids` are absent from the URL path (`'/' not in reportname`)
3. Extracts `active_ids` from the URL's `context` query parameter (where JS puts the action context)
4. Browses the wizard record using those `active_ids`
5. Evaluates `print_report_name` with the wizard record as `object`
6. Overrides the `Content-Disposition` header with the custom filename

### Data Flow Diagram

```
User clicks "Print" on wizard
        |
        v
check_report() -> _print_report()
        |
        v
report_action(self, data=data)  # self = wizard record
        |
        v
Returns action dict:
  {
    report_name: "accounting_pdf_reports.report_partnerledger",
    data: {form: {...}},
    context: {active_ids: [wizard_id], ...}
  }
        |
        v
JavaScript _getReportUrl():
  URL = /report/pdf/accounting_pdf_reports.report_partnerledger
        ?options={...}&context={"active_ids":[wizard_id],...}
        |
        v
POST /report/download
  data = [URL, "qweb-pdf"]
  context = user_context
        |
        v
ReportControllerExt.report_download():
  1. super() generates PDF with default filename
  2. Parse URL -> no docids in path
  3. Parse URL context -> active_ids = [wizard_id]
  4. Browse wizard -> evaluate print_report_name
  5. Override Content-Disposition header
        |
        v
Browser receives PDF with custom filename:
  "Kartica_partnera_BH_Telecom_Sarajevo.pdf"
```

## Filename Generation

### Method: `_get_report_base_filename()`

Located in `wizard/account_partner_ledger.py`:

```python
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
```

### Translation Strategy

The base filename uses `report.name` (the `name` field of `ir.actions.report`) instead of `_('Partner Ledger')` because:

1. The `name` field is a translatable `Char` stored as JSONB: `{"en_US": "Partner Ledger", "bs_BA": "Kartica partnera"}`
2. Reading `report.name` automatically returns the value for the user's current language
3. Code translations via `_()` can fail in `safe_eval` contexts where the caller frame doesn't resolve to the correct module

### Filename Examples

| Language | Partners Selected | Filename |
|----------|------------------|----------|
| bs_BA | BH Telecom Sarajevo | `Kartica_partnera_BH_Telecom_Sarajevo.pdf` |
| bs_BA | (none) | `Kartica_partnera.pdf` |
| en_US | BH Telecom Sarajevo | `Partner_Ledger_BH_Telecom_Sarajevo.pdf` |
| bs_BA | Partner A, Partner B | `Kartica_partnera_Partner_A_Partner_B.pdf` |

## Report XML Configuration

In `report/report.xml`:

```xml
<record id="action_report_partnerledger" model="ir.actions.report">
    <field name="name">Partner Ledger</field>
    <field name="model">account.report.partner.ledger</field>
    <field name="report_type">qweb-pdf</field>
    <field name="report_name">accounting_pdf_reports.report_partnerledger</field>
    <field name="print_report_name">object._get_report_base_filename()</field>
    <field name="paperformat_id" ref="paperformat_partner_ledger"/>
</record>
```

The `print_report_name` field requires both `en_US` and `bs_BA` keys in the database to avoid fallback issues:

```sql
-- Verify/fix in production:
UPDATE ir_act_report_xml
SET print_report_name = '{"en_US": "object._get_report_base_filename()", "bs_BA": "object._get_report_base_filename()}"'::jsonb
WHERE report_name = 'accounting_pdf_reports.report_partnerledger';
```

## Applicability

This controller override applies to **all reports** in the `accounting_pdf_reports` module that have `print_report_name` set. To add custom filenames to other wizard reports:

1. Add `print_report_name` to the report's XML record
2. Implement `_get_report_base_filename()` on the wizard model
3. The controller override will automatically evaluate it
