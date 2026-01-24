# Reports & Exports

## Available reports
- **Service Report**: Booking list with period and project filters
- **Single Booking Service Report**: Similar, with a dedicated PDF print format
- **Monthly Time Tracking Summary**: Monthly metrics per user
- **Yearly Time Tracking Summary**: Annual summary
- **Project Budget Overview**: Budget vs actuals and profitability

## Filters
Reports support period filters (day/week/month/range) and project/user filters where applicable.

## PDF export
The **Single Booking Service Report** provides a custom PDF print format for service reporting.

## Excel/CSV
Standard Frappe export options are available from report views. No custom Excel template is implemented.

## Admin export (Time Tracking Export)
Time Tracking Admins and System Managers have access to a dedicated export page with:
- CSV or XLSX output
- Date range filter
- Optional project filter (with child projects)
- Optional user filter
- Date format and decimal separator options

This export includes linked data (employee name and full project path) that is not present in the default Frappe export.
