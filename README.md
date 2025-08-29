# Odoomates Odoo Packages

This repository contains **12** Odoo packages from Odoomates vendor.

## About Odoomates

Odoomates is a recognized vendor in the Odoo ecosystem, providing specialized addons and customizations.

## Packages Included (12 packages)

- **odoo-bringout-odoomates-accounting_pdf_reports** - Accounting Pdf Reports
- **odoo-bringout-odoomates-om_account_accountant** - Om Account Accountant
- **odoo-bringout-odoomates-om_account_asset** - Om Account Asset
- **odoo-bringout-odoomates-om_account_budget** - Om Account Budget
- **odoo-bringout-odoomates-om_account_daily_reports** - Om Account Daily Reports
- **odoo-bringout-odoomates-om_account_followup** - Om Account Followup
- **odoo-bringout-odoomates-om_data_remove** - Om Data Remove
- **odoo-bringout-odoomates-om_fiscal_year** - Om Fiscal Year
- **odoo-bringout-odoomates-om_hospital** - Om Hospital
- **odoo-bringout-odoomates-om_mass_confirm_cancel** - Om Mass Confirm Cancel
- **odoo-bringout-odoomates-om_recurring_payments** - Om Recurring Payments
- **odoo-bringout-odoomates-task_check_list** - Task Check List


## Installation

Install any package from this collection:

```bash
# Install from local directory
pip install packages/odoomates/PACKAGE_NAME/

# Install in development mode  
pip install -e packages/odoomates/PACKAGE_NAME/

# Using uv (recommended for speed)
uv add packages/odoomates/PACKAGE_NAME/
```

## Repository Structure

Each package in this repository follows the standard Odoo addon structure:

```
odoomates/
├── odoo-bringout-odoomates-ADDON/
│   ├── ADDON_NAME/           # Complete addon code
│   │   ├── __init__.py
│   │   ├── __manifest__.py
│   │   └── ... (models, views, etc.)
│   ├── pyproject.toml        # Python package configuration
│   └── README.md            # Package documentation
└── ...
```

## License

Each package maintains its original license as specified by Odoomates.

## Support

For support with these packages, please refer to the original Odoomates documentation or community resources.
