# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    env["stock.picking"].search(
        [
            ("picking_type_code", "=", "outgoing"),
            ("state", "in", ("waiting", "confirmed", "assigned")),
            ("release_channel_id", "!=", False),
        ]
    )._compute_delivery_date()
