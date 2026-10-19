# Counterpoint POS

A multi-tenant retail platform built with React and FastAPI. The same inventory records drive purchases, barcode scanning, sales, returns and profit reporting. Configure a shop for supermarkets, fashion, footwear or general retail; products support open-ended categories, brands, variants, units, tax and expiry.

## Run locally

Requirements: Python 3.10+ and Node.js 18+.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
npm.cmd install
npm.cmd run dev
```

The React UI is at http://localhost:5173 and the API at http://localhost:8000. Interactive API documentation is at http://localhost:8000/docs.

To build the UI and serve it from FastAPI with one command:

```powershell
npm.cmd run start
```

The production UI and API are then available together at http://localhost:8000. SQLite data defaults to `retail_pos.db`. Set `DATABASE_PATH` to use a different location and set `SECRET_KEY` to a long random value before deployment.

## Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@demo.com` | `admin123` |
| Staff | `staff@demo.com` | `staff123` |

Demo accounts and example grocery products are seeded when the database is first created. Public store registration is disabled; local demo accounts are separate from the product-owner account. The isolated, read-only demo shop is available in every environment: admin `demo.admin@openkarts.in` / `DemoShop123!`, staff `demo.staff@openkarts.in` / `DemoStaff123!`. Demo users can browse products and reports but cannot create sales or change data. For local development only, the product-owner login defaults to `owner@demo.com` / `owner1234` when `DEMO_MODE=true`. Change these credentials for any shared development environment. Render sets `DEMO_MODE=false`, so production requires your own `PLATFORM_OWNER_EMAIL` and `PLATFORM_OWNER_PASSWORD` secrets.

## Shop workflow

1. **Products and stock:** maintain product brands, open-ended categories, size/colour variants, units, taxes, expiry dates, batches and reorder levels. Import CSV/XLSX files with row validation, generate Code 128 SKUs, print product or filtered bulk labels, and record stock adjustments.
2. **Suppliers and receiving:** keep supplier profiles, record invoice lines, tax, freight and payments, receive goods into stock, capture lot and expiry details, and calculate weighted-average cost including allocated freight.
3. **POS:** open a cashier shift with starting cash, scan/search barcodes, sell products, apply authorized discounts, calculate item taxes, collect cash/card/UPI/other payments, deduct stock and print receipts. Close the shift to reconcile cash against card and UPI sales.
4. **Sales returns:** refund eligible quantities, optionally restock returned products, and keep return and inventory movement history.
5. **Business finances:** record non-stock expenses and review monthly/yearly sales, tax, refunds, weighted-average COGS, estimated gross/operating profit and stock valuation.
6. **Team access:** admins can assign staff permissions for inventory, stock receiving, purchase costs, discounts and returns. Staff sales and sales history are restricted to their own activity; store-wide financial reports remain admin-only.

CSV/XLSX imports accept a header row with `name`, `category`, `sku`, `price`, and `stock`; optional columns are `brand`, `size`, `color`, `unit`, `tax_rate`, `expiry_date`, `cost`, and `reorder_level`. Blank SKUs are generated. An import is all-or-nothing; validation errors identify row numbers.

## Onboarding multiple retail shops

The product owner signs in using **Platform owner sign in** on the shared application URL. Configure a strong `PLATFORM_OWNER_EMAIL` and `PLATFORM_OWNER_PASSWORD` before deployment. From **Shop workspaces**, the product owner creates each retailer's tenant and initial owner/admin login, then privately shares that shop's credentials with its owner. Public registration is disabled, so visitors cannot create their own stores. Each tenant's inventory, staff, sales, purchases and reports are isolated. Shop owners add their own employees from **Team** and assign permissions. The product owner can suspend or reactivate a shop without deleting its data. Visitors can use the separate read-only demo accounts to explore sample products and reports without changing demo or customer data.

For production, deploy one shared Render service and custom domain and configure the product-owner credentials in Render's environment settings. Keep Razorpay POS payment keys configured at the service level. SaaS subscription plans, recurring subscription billing, and automated shop billing are not implemented yet; Razorpay here is for customer checkout at the POS.

Admins can change the app accent color from the color selector in the top bar; the preference is saved per signed-in user on that browser. Reports can be filtered by date and downloaded as CSV.

## API architecture

```text
app/
  controllers/   FastAPI route handlers
  dbconfig/      SQLite connections, schema and migrations
  logger/        Application logging
  middleware/    Authentication, permission checks and request logging
  models/        Validated API schemas
  repositories/  Database reads and transactional writes
  services/      Business rules and workflows
  utils/         Security helpers
frontend/
  src/           React interface and styles
```

## Razorpay payments

Set `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` to enable the POS's online Razorpay Checkout option. Set `RAZORPAY_WEBHOOK_SECRET` and create a Razorpay webhook for `https://pos.openkarts.in/api/payments/razorpay/webhook` with the `payment.captured` event enabled. Checkout signatures are checked by the API, payment capture and amount are confirmed against Razorpay, and repeated confirmations do not create duplicate sales. Keep live keys in Render's environment settings; use test-mode keys for development.

## Deploy to Render

The root `render.yaml` provisions the Docker web service, `/api/health` health check, required environment variables and persistent disk for SQLite. Push the repository to GitHub, create a Blueprint on Render from the repo, then enter platform-owner and Razorpay credentials when prompted. Use a unique, strong password for the product owner and never commit it. The configured public origin for both the React app and relative `/api` endpoints is `https://pos.openkarts.in`.

After the first deploy, add `pos.openkarts.in` as the service's custom domain in the Render dashboard and configure the DNS records Render shows at your DNS provider. Render issues HTTPS for the domain. Then configure the Razorpay webhook URL above. The domain and payment credentials must be configured in Render; repository YAML cannot point DNS or supply private gateway keys.

Render's deployment sets `DEMO_MODE=false`: public production deployments do not seed the shared demo accounts. For isolated local demo data, the development default is `DEMO_MODE=true`; turn it off when using a production database.

This is a deployment-ready starter, not a certified accounting or tax product. Configure and review applicable GST/tax invoices, payment gateway account settings, backups, printer hardware and security policies before commercial use.
