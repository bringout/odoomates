# Same cleanup as hooks.pre_init_hook, but for the upgrade path:
# whenever this module is upgraded (e.g. when a downstream --init/--update
# of an accounting_pdf_reports re-init walks the dependency graph and
# re-loads security/group.xml here), drop the B2C tax-display group
# from any user that also has the B2B one, so account._check_one_user_type
# doesn't trip on the implied_ids change.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        SELECT
            (SELECT res_id FROM ir_model_data
             WHERE module='account'
               AND name='group_show_line_subtotals_tax_included'),
            (SELECT res_id FROM ir_model_data
             WHERE module='account'
               AND name='group_show_line_subtotals_tax_excluded')
    """)
    row = cr.fetchone()
    if not row or not all(row):
        return
    g_included, g_excluded = row

    cr.execute("""
        SELECT uid FROM res_groups_users_rel WHERE gid = %s
        INTERSECT
        SELECT uid FROM res_groups_users_rel WHERE gid = %s
    """, (g_included, g_excluded))
    conflicting = [r[0] for r in cr.fetchall()]
    if not conflicting:
        return

    _logger.info(
        "om_account_accountant pre-migration: dropping B2C tax group "
        "from %d user(s) with both B2B and B2C set: %s",
        len(conflicting), conflicting,
    )
    cr.execute(
        "DELETE FROM res_groups_users_rel WHERE gid = %s AND uid = ANY(%s)",
        (g_included, conflicting),
    )
