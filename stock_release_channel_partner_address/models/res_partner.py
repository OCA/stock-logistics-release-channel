# Copyright 2025 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models
from odoo.osv.expression import AND


class ResPartner(models.Model):
    _inherit = "res.partner"

    @property
    def _release_channel_possible_candidate_domain(self):
        # OVERRIDE: allow only channels matching the partner's address
        # For both country and state, a match is achieved if:
        # - the partner's country or state is included in the channel's ones
        # - the partner's country or state is not defined
        domain = super()._release_channel_possible_candidate_domain
        if country := self.country_id:
            domain = AND(
                [
                    domain,
                    [
                        "|",
                        ("country_ids", "=", False),
                        ("country_ids", "in", country.ids),
                    ],
                ]
            )
        if state := self.state_id:
            domain = AND(
                [
                    domain,
                    ["|", ("state_ids", "=", False), ("state_ids", "in", state.ids)],
                ]
            )
        return domain
