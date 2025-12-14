# Odoo HR Commission Module (`hr_commission`)

## Project Overview

This directory contains the `hr_commission` Odoo module. It's an extension for the Odoo ERP system, designed to integrate the `sale_commission` and `hr` (Human Resources) modules. The primary purpose is to enable the assignment of sales commissions to employees.

The module extends the `res.partner` model (used for customers, vendors, and agents) to allow a partner to be designated as a "Salesman (employee)". This creates a direct link between a sales agent and an employee record in the HR module. This link is crucial for managing and tracking commissions earned by employees.

**Key Features:**

*   Adds a "Salesman (employee)" option to the agent type on the partner form.
*   Links partners to employee records.
*   Includes logic to ensure that a "Salesman (employee)" is linked to a valid employee.
*   Provides a mechanism to mark commission settlements as "invoiced".

**Technologies:**

*   **Odoo Framework (Python):** The module is built using the Odoo framework, which is based on Python.
*   **XML:** Odoo uses XML files to define user interfaces (views), data, and configuration.

**Architecture:**

The module follows the standard Odoo module structure:

*   `__manifest__.py`: The module's manifest file, which defines its metadata and dependencies.
*   `models/`: Contains the Python files that define the data models (e.g., `hr.employee`, `res.partner`).
*   `views/`: Contains the XML files that define the user interface.
*   `tests/`: Contains the Python files for testing the module's functionality.
*   `i18n/`: Contains translation files.

## Building and Running

This is an Odoo module and is not a standalone application. It needs to be installed in an Odoo environment that has the `sale_commission` and `hr` modules installed.

**To use this module:**

1.  Add the `hr_commission` directory to the `addons_path` of your Odoo configuration.
2.  Restart the Odoo server.
3.  Go to the "Apps" menu in Odoo.
4.  Remove the "Apps" filter and search for "HR commissions".
5.  Click the "Install" button.

**Running Tests:**

Odoo's testing framework is used to run the tests for this module. To run the tests, you would typically use the following command line option when starting the Odoo server:

```bash
odoo --test-enable --stop-after-init -i hr_commission
```

This command will initialize the `hr_commission` module, run its tests, and then stop the server.

## Development Conventions

The code follows the standard Odoo development guidelines.

*   **Models:** The data models are defined in the `models/` directory. Each file corresponds to a model or a set of related models.
*   **Views:** The user interface is defined in the `views/` directory. The XML files define the forms, lists, and other views for the models.
*   **Tests:** The tests are written using the `odoo.tests.common.TransactionCase` class. They are located in the `tests/` directory.
*   **Commits:** The commit messages should be clear and descriptive. They should explain the purpose of the change.
*   **Licensing:** The module is licensed under the AGPL-3 license.
