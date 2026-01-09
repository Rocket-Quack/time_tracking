<div align="center">
  <p>
    <img src="docs/assets/TIME_TRACKING_APP_LOGO.png" alt="Time Tracking App Logo" width="164"/>
  </p>
  <h1>Time Tracking (Frappe App)</h1>
</div>

Time Tracking is a Frappe app for web-based time tracking and timesheet management.

Teams can record work hours, manage timesheets, generate reports, and export data for invoicing and payroll workflows.



## Supported Versions

| Frappe | Support Status |
|--------|----------------|
| v16 Beta | Coming soon... |
| v15 | Coming soon... |

## Installation (Frappe Cloud)

The app can be installed directly via Frappe Cloud:

1. Open the Frappe Cloud dashboard at <https://frappecloud.com/dashboard/#/sites>
2. Click **"New Site"** to create a new site
3. In the step **"Select apps to install"**:
   - Choose the desired Frappe version
   - Enable the app **`Time Tracking`**
4. Complete the wizard to create the site

## Installation (Self-Hosted)

Add the app to your bench environment:

```bash
bench get-app https://github.com/Rocket-Quack/time_tracking.git --branch version-15
```

Install requirements:

```bash
bench setup requirements
```

Install the app on a site:

```bash
bench --site yoursite.com install-app time_tracking
```

Run migrations:

```bash
bench --site yoursite.com migrate
```

## Community Support

Please create a ticket via [Issues](https://github.com/Rocket-Quack/erpnext_sumup/issues) for:

- **Bug Reports & Feature Requests** 
- **Questions about general use**

## Trademark Notice

**Frappe** is a trademark of **Frappe Technologies Pvt. Ltd.**

This project is an independent and unofficial app and is not affiliated with Frappe Technologies.
It is not operated, supported, or endorsed by Frappe Technologies.

The name Frappe is used only to describe technical compatibility with the respective framework.

### License

See the LICENSE file for more information.
