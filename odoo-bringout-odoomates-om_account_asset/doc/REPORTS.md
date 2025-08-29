# Reports

Report definitions and templates in om_account_asset.

```mermaid
classDiagram
    class AssetAssetReport
    Model <|-- AssetAssetReport
```

## Available Reports

### Analytical/Dashboard Reports
- **Assets Analysis** (Analysis/Dashboard)


## Report Files

- **account_asset_report.py** (Python logic)
- **account_asset_report_views.xml** (XML template/definition)
- **__init__.py** (Python logic)

## Notes
- Named reports above are accessible through Odoo's reporting menu
- Python files define report logic and data processing
- XML files contain report templates, definitions, and formatting
- Reports are integrated with Odoo's printing and email systems
