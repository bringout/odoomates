"""Drop the obsolete v16 res.config.settings budget override before the v16->v19 reload.

v16 om_account_budget shipped a res.config.settings inherit
(``res_config_settings_view_form``, name
"res.config.settings.view.form.inherit.account.budget") whose arch does
``<xpath expr="//div[@id='account_budget']">``. v19 removed that settings
``<div id="account_budget">`` (the v19 module no longer defines the override
— see views/res_config_settings_views.xml), but Odoo only deletes such
obsolete records at the END of the module load (``_process_end``) while it
re-combines and re-validates res.config.settings EARLIER in the upgrade — so
the leftover v16 view fails: "Element <xpath expr=//div[@id='account_budget']>
cannot be located in parent view". Dropping it up front removes it before any
re-validation. (Same obsolete-view-on-upgrade gotcha as l10n_ba_hr_timesheet.)
"""


def migrate(cr, version):
    cr.execute(
        """
        DELETE FROM ir_ui_view
        WHERE id IN (
            SELECT res_id FROM ir_model_data
            WHERE module = 'om_account_budget'
              AND model = 'ir.ui.view'
              AND name = 'res_config_settings_view_form'
        )
        """
    )
    cr.execute(
        """
        DELETE FROM ir_model_data
        WHERE module = 'om_account_budget'
          AND model = 'ir.ui.view'
          AND name = 'res_config_settings_view_form'
        """
    )
