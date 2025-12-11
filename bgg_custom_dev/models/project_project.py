# -*- coding: utf-8 -*-

import logging
from odoo import api, models

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to trigger automation rules on new projects"""
        records = super(ProjectProject, self).create(vals_list)

        for record in records:
            self._update_project_folder_name(record)

        return records

    def _update_project_folder_name(self, record):
        """
        Update Project Folder Name - Automation Rule
        Renames the project's documents folder based on sales order and customer name
        Format: SO Name - Projet - Customer Name
        """
        try:
            # Only process if this is a new record (newly created project from template)
            if not (record.create_date == record.write_date):
                return

            _logger.info("Processing new project (ID %s): %s", record.id, record.name)

            # Check if project has an associated sale order line
            if record.sale_line_id:
                # Get the sales order and client information
                sale_order = record.sale_line_id.order_id
                customer = sale_order.partner_id

                # Check if we have a documents folder created
                if record.documents_folder_id:
                    # Create new folder name with SO reference and client name
                    new_folder_name = f"{sale_order.name} - Projet - {customer.name}"

                    if record.documents_folder_id.name != new_folder_name:
                        record.documents_folder_id.write({
                            'name': new_folder_name
                        })
                        _logger.info("Updated project folder name to: '%s' for project ID %s",
                                   new_folder_name, record.id)
                    else:
                        _logger.info("Project folder name already correct for project ID %s", record.id)
                else:
                    _logger.warning("No documents folder found for project ID %s", record.id)
            else:
                _logger.info("No sale order line linked to project ID %s, skipping folder rename", record.id)

        except Exception as e:
            _logger.error("Update Project Folder Name - Error processing project ID %s: %s",
                        record.id, str(e), exc_info=True)
