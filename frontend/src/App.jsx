import { useCallback, useEffect, useRef, useState } from "react";
import JsBarcode from "jsbarcode";
import {
  AlertTriangle, ArrowDownRight, ArrowRight, ArrowUpRight, Barcode, BarChart3,
  Bell, Check, ChevronDown, ChevronLeft, ChevronRight, CircleDollarSign, Download,
  ClipboardList, CreditCard, Eye, EyeOff, FileSpreadsheet, LayoutDashboard, LogOut, Minus, Package,
  Palette, Plus, Printer, Search, Settings2, ShieldCheck, ShoppingBag, ShoppingCart,
  Store, Tag, Trash2, TrendingUp, UserRound, Users, X, Truck, Wallet, RotateCcw,
} from "lucide-react";

const money = (value) => new Intl.NumberFormat("en-US", { style: "currency", currency: localStorage.getItem("counterpoint_currency") || "INR" }).format(Number(value || 0));
const dateTime = (value) => new Date(value).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
const API = "/api";
const THEMES = [
  ["forest", "Forest"],
  ["ocean", "Ocean"],
  ["berry", "Berry"],
  ["plum", "Plum"],
  ["amber", "Amber"],
];
const STAFF_PERMISSIONS = [
  ["manage_inventory", "Manage inventory", "Add and update products, import items, and adjust stock."],
  ["receive_stock", "Receive stock & manage suppliers", "Record supplier invoices and incoming goods."],
  ["view_purchase_costs", "View purchase costs", "See unit costs and inventory valuation."],
  ["apply_discounts", "Apply checkout discounts", "Apply discounts when billing customers."],
  ["process_returns", "Process returns", "Refund sales and return items to stock."],
];

async function request(path, token, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  const data = response.status === 204 ? null : await response.json();
  if (!response.ok) throw new Error(data?.detail || "Something went wrong. Please try again.");
  return data;
}

function BarcodeImage({ value, className = "" }) {
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current && value) {
      try { JsBarcode(ref.current, value, { format: "CODE128", displayValue: true, fontSize: 12, height: 48, margin: 4, width: 1.6 }); }
      catch { ref.current.innerHTML = ""; }
    }
  }, [value]);
  return <svg ref={ref} className={className} aria-label={`Barcode ${value}`} />;
}

function printProductLabel(product) {
  printProductLabels([product]);
}

function printProductLabels(products) {
  if (!products.length) return;
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  const barcodes = products.map((product) => {
    const barcode = svg.cloneNode(false);
    JsBarcode(barcode, product.sku, { format: "CODE128", displayValue: true, fontSize: 11, height: 34, margin: 2, width: 1.4 });
    return { ...product, barcode: barcode.outerHTML };
  });
  const escapeHtml = (value) => String(value || "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[character]));
  const labels = barcodes.map((product) => {
    const details = [product.size, product.color].filter(Boolean).join(" / ");
    return `<article class="label"><div class="name">${escapeHtml(product.name)}</div><div class="details">${escapeHtml(details)}</div><div class="price">${money(product.price)}</div>${product.barcode}<div>SKU: ${escapeHtml(product.sku)}</div></article>`;
  }).join("");
  const printWindow = window.open("", "_blank", "width=360,height=260");
  if (!printWindow) throw new Error("Allow pop-ups to print barcode labels.");
  printWindow.document.write(`<html><head><title>Product barcode labels</title><style>@page{size:60mm 35mm;margin:2mm}body{font:9px Arial;text-align:center;color:#111;display:grid;grid-template-columns:repeat(3,60mm);gap:1mm}.label{width:56mm;height:31mm;overflow:hidden;page-break-inside:avoid}.name{font-weight:bold;font-size:10px}.details{margin-top:1px}.price{font-weight:bold;margin-top:1px}svg{max-width:100%;height:auto}</style></head><body>${labels}<script>window.onload=()=>{window.print();window.onafterprint=()=>window.close()}<\/script></body></html>`);
  printWindow.document.close();
}

function Auth({ onAuth }) {
  const [platformLogin, setPlatformLogin] = useState(false);
  const [demoAccounts, setDemoAccounts] = useState([]);
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const update = (key) => (event) => setForm({ ...form, [key]: event.target.value });
  useEffect(() => {
    request("/auth/config", null)
      .then((config) => setDemoAccounts(config.demo_accounts || []))
      .catch(() => setDemoAccounts([]));
  }, []);
  function fillCredentials(email, password) {
    setForm({ email, password });
    setError("");
    setShowPassword(false);
  }
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const result = await request(platformLogin ? "/auth/platform/login" : "/auth/login", null, {
        method: "POST", body: JSON.stringify({ email: form.email, password: form.password }),
      });
      onAuth(result);
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  return <main className="auth-shell">
    <section className="auth-card">
      <aside className="auth-story">
        <a className="auth-brand" href="#"><span className="auth-brand-mark"><Store size={22} /></span><span>OpenKarts<small>RETAIL, ALL TOGETHER</small></span></a>
        <div className="auth-orbit auth-orbit-one" /><div className="auth-orbit auth-orbit-two" /><div className="auth-glow" />
        <div className="auth-story-copy">
          <span className="auth-kicker"><i /> RETAIL, MADE SIMPLE</span>
          <h1>{platformLogin ? <>Your shops.<br />One clear view.</> : <>Everything your shop needs,<br /><em>all in one place.</em></>}</h1>
          <p>{platformLogin ? "Create and manage retailer workspaces from your own secure platform." : "Products, stock, and sales—working together so you can focus on your customers."}</p>
          <div className="auth-feature-row"><span><Barcode size={16} /> Smart inventory</span><span><ShoppingCart size={16} /> Fast checkout</span><span><BarChart3 size={16} /> Clear reports</span></div>
        </div>
        <div className="auth-story-footer"><span className="auth-footer-dot" /> MADE FOR EVERY KIND OF SHOP</div>
      </aside>
      <section className="auth-panel">
        <div className="auth-mobile-brand"><span className="auth-brand-mark"><Store size={19} /></span><span>OpenKarts<small>RETAIL POS</small></span></div>
        <div className="auth-form-wrap">
          <div className="auth-heading"><span className="auth-form-kicker">{platformLogin ? "PLATFORM OWNER" : "YOUR RETAIL WORKSPACE"}</span>
            <h2>{platformLogin ? "Welcome back." : "Welcome back!"}</h2>
            <p>{platformLogin ? "Sign in to manage your retailer accounts." : "Sign in to continue to your shop."}</p>
          </div>
          <form onSubmit={submit} className="auth-form">
            <label>{platformLogin ? "Product owner email" : "Email address"}<input type="email" required value={form.email} onChange={update("email")} placeholder="you@example.com" autoComplete="username" /></label>
            <label>Password<span className="auth-password-wrap"><input type={showPassword ? "text" : "password"} required value={form.password} onChange={update("password")} placeholder="Enter your password" autoComplete="current-password" /><button type="button" className="password-visibility" onClick={() => setShowPassword((visible) => !visible)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={19} /> : <Eye size={19} />}</button></span></label>
            {error && <div className="inline-error">{error}</div>}
            <button className="auth-submit" disabled={busy}>{busy ? "Signing you in..." : platformLogin ? "Sign in to platform" : "Sign in"}<ArrowRight size={18} /></button>
          </form>
          {!platformLogin && demoAccounts.length > 0 && <div className="auth-demo"><div className="auth-demo-heading"><ShieldCheck size={16} /><b>Try the read-only demo shop</b></div>{demoAccounts.map((account) => <button type="button" key={account.email} onClick={() => fillCredentials(account.email, account.password)}><span>{account.label}</span><code>{account.email} · {account.password}</code><b>Fill</b></button>)}<p>Explore the shop with sample products. Demo data cannot be changed.</p></div>}
          <div className="auth-switch">{platformLogin ? "Looking for your shop?" : "Are you the product owner?"} <button onClick={() => { setPlatformLogin(!platformLogin); setError(""); setForm({ email: "", password: "" }); setShowPassword(false); }}>{platformLogin ? "Shop sign in" : "Platform owner sign in"}</button></div>
          {!platformLogin && <p className="auth-access-note">New shop accounts are set up by the OpenKarts product owner.</p>}
        </div>
        <div className="auth-foot">SECURE SIGN IN <span>© 2026 OpenKarts POS</span></div>
      </section>
    </section>
  </main>;
}

function StatCard({ title, value, foot, icon: Icon, tint = "sage", trend }) {
  return <article className="stat-card"><div className="stat-top"><span>{title}</span><span className={`stat-icon ${tint}`}><Icon size={18} /></span></div>
    <div className="stat-value">{value}</div><div className="stat-foot">{trend && <span className="trend"><ArrowUpRight size={13} />{trend}</span>}{foot}</div>
  </article>;
}

function Modal({ title, subtitle, onClose, children, wide = false }) {
  return <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
    <section className={`modal ${wide ? "modal-wide" : ""}`}><header className="modal-head"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div><button className="icon-button" onClick={onClose} aria-label="Close"><X size={19} /></button></header>{children}</section>
  </div>;
}

function ProductForm({ product, onSave, onClose, canViewCosts = true }) {
  const [form, setForm] = useState(product || { name: "", brand: "", category: "General", sku: "", size: "", color: "", unit: "each", tax_rate: "0", expiry_date: "", price: "", cost: "", stock: "", reorder_level: "5" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const change = (key) => (event) => setForm({ ...form, [key]: event.target.value });
  function makeBarcode() { setForm({ ...form, sku: `CP${Date.now().toString().slice(-9)}` }); }
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError("");
    try { await onSave({ ...form, price: Number(form.price), cost: Number(form.cost || 0), stock: Number(form.stock), reorder_level: Number(form.reorder_level || 5) }); onClose(); }
    catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  return <form className="modal-form" onSubmit={submit}>
    <div className="form-grid"><label>Product name<input required maxLength="160" value={form.name} onChange={change("name")} placeholder="e.g. House blend coffee" /></label>
      <label>Brand<input maxLength="100" value={form.brand || ""} onChange={change("brand")} placeholder="e.g. Northstar" /></label>
      <label>Category<input maxLength="80" value={form.category} onChange={change("category")} placeholder="e.g. Pantry" /></label>
      <label className="field-span">Barcode / SKU<div className="input-action"><input required value={form.sku} onChange={change("sku")} placeholder="Scan or enter a code" /><button type="button" className="button button-quiet" onClick={makeBarcode}><Barcode size={16} /> Generate</button></div></label>
      <label>Size / variant<input maxLength="40" value={form.size || ""} onChange={change("size")} placeholder="e.g. EU 38, 500 ml" /></label>
      <label>Color<input maxLength="40" value={form.color || ""} onChange={change("color")} placeholder="e.g. Navy, Black" /></label>
      <label>Unit<input maxLength="24" value={form.unit || "each"} onChange={change("unit")} placeholder="each, kg, litre" /></label>
      <label>Tax rate (%)<input type="number" min="0" max="100" step="0.01" value={form.tax_rate ?? 0} onChange={change("tax_rate")} /></label>
      <label>Expiry date<input type="date" value={form.expiry_date || ""} onChange={change("expiry_date")} /></label>
      <label>Selling price<input type="number" required min="0.01" step="0.01" value={form.price} onChange={change("price")} placeholder="0.00" /></label>
      {canViewCosts && <label>Cost per unit<input type="number" min="0" step="0.01" value={form.cost ?? ""} onChange={change("cost")} placeholder="0.00" /></label>}
      <label>In stock<input type="number" required min="0" step="0.001" value={form.stock} onChange={change("stock")} placeholder="0" /></label>
      <label>Low-stock alert at<input type="number" min="0" step="0.001" value={form.reorder_level} onChange={change("reorder_level")} placeholder="5" /></label>
    </div>
    {form.sku && <div className="barcode-preview"><span className="eyebrow">BARCODE PREVIEW</span><BarcodeImage value={form.sku} /></div>}
    {error && <div className="inline-error">{error}</div>}
    <footer className="modal-actions"><button type="button" className="button button-quiet" onClick={onClose}>Cancel</button><button disabled={busy} className="button button-primary">{busy ? "Saving..." : product ? "Save changes" : "Add product"}</button></footer>
  </form>;
}

function StaffForm({ onSave, onClose }) {
  const [form, setForm] = useState({ name: "", email: "", password: "", permissions: {} });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const change = (key) => (event) => setForm({ ...form, [key]: event.target.value });
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError("");
    try { await onSave(form); onClose(); } catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  return <form className="modal-form" onSubmit={submit}><div className="form-stack">
    <label>Full name<input required minLength="2" value={form.name} onChange={change("name")} placeholder="Jordan Lee" /></label>
    <label>Email address<input type="email" required value={form.email} onChange={change("email")} placeholder="jordan@yourstore.com" /></label>
    <label>Temporary password<input type="password" minLength="8" required value={form.password} onChange={change("password")} placeholder="At least 8 characters" /></label>
    <PermissionFields permissions={form.permissions} onChange={(permissions) => setForm({ ...form, permissions })} />
  </div>{error && <div className="inline-error">{error}</div>}<footer className="modal-actions"><button type="button" className="button button-quiet" onClick={onClose}>Cancel</button><button disabled={busy} className="button button-primary">{busy ? "Adding..." : "Add staff member"}</button></footer></form>;
}

function PermissionFields({ permissions, onChange }) {
  return <fieldset className="permission-fields"><legend>Optional permissions</legend>{STAFF_PERMISSIONS.map(([key, title, description]) => <label className="permission-option" key={key}><input type="checkbox" checked={Boolean(permissions?.[key])} onChange={(event) => onChange({ ...permissions, [key]: event.target.checked })} /><span><b>{title}</b><small>{description}</small></span></label>)}</fieldset>;
}

function PermissionsForm({ staff, onSave, onClose }) {
  const [permissions, setPermissions] = useState(staff.permissions || {});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError("");
    try { await onSave(permissions); onClose(); } catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  return <form className="modal-form" onSubmit={submit}><PermissionFields permissions={permissions} onChange={setPermissions} />{error && <div className="inline-error">{error}</div>}<footer className="modal-actions"><button type="button" className="button button-quiet" onClick={onClose}>Cancel</button><button disabled={busy} className="button button-primary">{busy ? "Saving..." : "Save permissions"}</button></footer></form>;
}

function Receipt({ sale, user, store, onClose }) {
  return <Modal title="Sale complete" subtitle={`Receipt #${String(sale.id).padStart(5, "0")}`} onClose={onClose}>
    <div className="receipt-print-target">
      <div className="receipt-brand">{store}<span>Thanks for shopping local!</span></div>
      <div className="receipt-meta"><span>Receipt #{String(sale.id).padStart(5, "0")}</span><span>{dateTime(sale.created_at)}</span><span>Served by {user.name}</span></div>
      <div className="receipt-lines">{sale.items.map((item, index) => <div className="receipt-line" key={`${item.product_id}-${index}`}><span>{item.product_name}{item.variant ? ` (${item.variant})` : ""} × {item.quantity}</span><b>{money(item.line_total)}</b></div>)}</div>
      <div className="receipt-total"><div><span>Subtotal</span><span>{money(sale.subtotal)}</span></div>{sale.discount > 0 && <div><span>Discount</span><span>-{money(sale.discount)}</span></div>}{sale.tax > 0 && <div><span>Tax</span><span>{money(sale.tax)}</span></div>}<div className="receipt-grand"><b>Total</b><b>{money(sale.total)}</b></div><div><span>Payment · {sale.payment_method}</span><span>Paid</span></div></div>
      <div className="receipt-thanks">We appreciate you. Come back soon.</div>
    </div>
    <footer className="modal-actions receipt-buttons"><button className="button button-quiet" onClick={onClose}>Done</button><button className="button button-primary" onClick={() => window.print()}><Printer size={16} /> Print receipt</button></footer>
  </Modal>;
}

function AppShell({ token, user, onLogout }) {
  const themeKey = `counterpoint_theme_${user.id}`;
  const [theme, setTheme] = useState(() => localStorage.getItem(themeKey) || "forest");
  const [page, setPage] = useState(user.role === "admin" ? "Overview" : "Point of sale");
  const [dashboard, setDashboard] = useState(null);
  const [products, setProducts] = useState([]);
  const [sales, setSales] = useState([]);
  const [staff, setStaff] = useState([]);
  const [categories, setCategories] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [lowOnly, setLowOnly] = useState(false);
  const [version, setVersion] = useState(0);
  const [modal, setModal] = useState("");
  const [editingProduct, setEditingProduct] = useState(null);
  const [toast, setToast] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const refresh = useCallback(() => setVersion((value) => value + 1), []);

  useEffect(() => {
    let active = true;
    setLoading(true); setError("");
    const load = async () => {
      try {
        const [dash, productList, saleList, categoryList, team] = await Promise.all([
          user.role === "admin" ? request("/dashboard", token) : Promise.resolve(null), request("/products", token), request("/sales", token),
          request("/categories", token), user.role === "admin" ? request("/staff", token) : Promise.resolve([]),
        ]);
        if (active) { setDashboard(dash); setProducts(productList); setSales(saleList); setCategories(categoryList); setStaff(team); }
      } catch (err) { if (active) setError(err.message); }
      finally { if (active) setLoading(false); }
    };
    load(); return () => { active = false; };
  }, [token, user.role, version]);

  useEffect(() => { if (!toast) return; const timeout = setTimeout(() => setToast(""), 3000); return () => clearTimeout(timeout); }, [toast]);
  const admin = user.role === "admin";
  const nav = [
    { section: "WORKSPACE", items: [...(admin ? [{ name: "Overview", icon: LayoutDashboard }] : []), { name: "Point of sale", icon: ShoppingCart }, { name: "Inventory", icon: Package }, { name: "Sales", icon: ClipboardList }] },
    ...(admin || user.permissions?.receive_stock ? [{ section: "MANAGE", items: [...(admin ? [{ name: "Reports", icon: BarChart3 }, { name: "Expenses", icon: Wallet }, { name: "Team", icon: Users }] : []), { name: "Purchases", icon: Truck }, { name: "Suppliers", icon: Users }] }] : []),
  ];
  async function saveProduct(data) {
    await request(editingProduct ? `/products/${editingProduct.id}` : "/products", token, { method: editingProduct ? "PUT" : "POST", body: JSON.stringify(data) });
    setToast(editingProduct ? "Product updated" : "Product added"); refresh();
  }
  async function deleteProduct(product) {
    if (!window.confirm(`Remove ${product.name} from your inventory?`)) return;
    try { await request(`/products/${product.id}`, token, { method: "DELETE" }); setToast("Product removed"); refresh(); }
    catch (err) { setToast(err.message); }
  }
  async function addStaff(data) { await request("/staff", token, { method: "POST", body: JSON.stringify(data) }); setToast("Team member added"); refresh(); }
  async function updateStaffPermissions(member, permissions) {
    await request(`/staff/${member.id}/permissions`, token, { method: "PUT", body: JSON.stringify({ permissions }) });
    setToast(`Permissions updated for ${member.name}`); refresh();
  }
  async function importProducts(file) {
    const formData = new FormData(); formData.append("file", file);
    const response = await fetch(`${API}/products/import`, { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: formData });
    const result = await response.json();
    if (!response.ok) throw new Error(typeof result.detail === "string" ? result.detail : result.detail?.message || "Import failed. Check the file and try again.");
    setToast(`${result.imported} products imported`); refresh();
  }
  async function createSale(data) {
    const sale = await request("/sales", token, { method: "POST", body: JSON.stringify(data) });
    setModal("receipt"); setLastSale(sale); setToast("Sale recorded — inventory updated"); refresh();
    return sale;
  }
  function completeRazorpaySale(sale) {
    setLastSale(sale); setModal("receipt"); setToast("Razorpay payment confirmed — inventory updated"); refresh();
  }
  const [lastSale, setLastSale] = useState(null);
  const visibleProducts = products.filter((product) => {
    const matchesSearch = !search || `${product.name} ${product.sku} ${product.category}`.toLowerCase().includes(search.toLowerCase());
    return matchesSearch && (category === "All" || product.category === category) && (!lowOnly || product.stock <= product.reorder_level);
  });
  function changeTheme(event) {
    const nextTheme = event.target.value;
    setTheme(nextTheme);
    localStorage.setItem(themeKey, nextTheme);
  }
  return <div className="app-shell" data-theme={theme}>
    <aside className="sidebar">
      <a className="brand" href="#" onClick={(event) => { event.preventDefault(); setPage("Overview"); }}><span className="brand-mark"><Store size={19} /></span><span>counterpoint<small>RETAIL, MADE SIMPLE</small></span></a>
      <div className="store-switch"><span className="store-avatar">{(user.store_name || "S").slice(0, 1).toUpperCase()}</span><span className="store-info"><b>{user.store_name}</b><small>{admin ? "Admin workspace" : "Staff workspace"}</small></span><ChevronDown size={15} /></div>
      <nav className="side-nav">{nav.map((group) => <div key={group.section}><div className="nav-section">{group.section}</div>{group.items.map(({ name, icon: Icon }) => <button key={name} className={`nav-item ${page === name ? "active" : ""}`} onClick={() => setPage(name)}><Icon size={18} /><span>{name}</span>{name === "Inventory" && dashboard?.low_stock > 0 && <i className="nav-count">{dashboard.low_stock}</i>}</button>)}</div>)}</nav>
      <div className="sidebar-bottom"><div className="help-card"><span className="help-icon"><Settings2 size={16} /></span><div><b>Need a hand?</b><small>We're here for you.</small></div><ArrowRight size={15} /></div>
        <div className="profile-row"><div className="profile-avatar">{user.name.split(" ").map((part) => part[0]).join("").slice(0, 2)}</div><div className="profile-copy"><b>{user.name}</b><small>{user.role === "admin" ? "Store admin" : "Team member"}</small></div><button className="icon-button logout-button" title="Sign out" aria-label="Sign out" onClick={onLogout}><LogOut size={17} /></button></div>
      </div>
    </aside>
    <main className="main-panel">
      <header className="topbar"><div className="breadcrumb">Workspace <ChevronRight size={14} /><b>{page}</b></div><div className="topbar-actions"><span className="today-label">{new Date().toLocaleDateString([], { weekday: "long", month: "long", day: "numeric" })}</span><label className="theme-picker"><Palette size={16} /><span className="visually-hidden">App color theme</span><select aria-label="App color theme" value={theme} onChange={changeTheme}>{THEMES.map(([value, label]) => <option value={value} key={value}>{label} theme</option>)}</select></label><button className="button button-quiet signout-button" onClick={onLogout}><LogOut size={15} /><span>Sign out</span></button></div></header>
      <div className="page-content">
        {user.is_demo && <div className="demo-readonly-banner"><ShieldCheck size={18} /><span><b>Read-only demo shop</b>Explore sample inventory, sales, and reports. Changes are disabled and cannot affect retailer accounts.</span></div>}
        {error && <div className="error-banner"><AlertTriangle size={17} />{error}<button className="text-button" onClick={refresh}>Try again</button></div>}
        {loading && !dashboard ? <div className="loading-state"><span className="spinner" />Getting things ready...</div> : <>
          {page === "Overview" && <Overview dashboard={dashboard} user={user} onNavigate={setPage} sales={sales} />}
          {page === "Inventory" && <Inventory products={visibleProducts} categories={categories} category={category} setCategory={setCategory} search={search} setSearch={setSearch} lowOnly={lowOnly} setLowOnly={setLowOnly} admin={admin} canManage={admin || user.permissions?.manage_inventory} onAdd={() => { setEditingProduct(null); setModal("product"); }} onEdit={(product) => { setEditingProduct(product); setModal("product"); }} onDelete={deleteProduct} onImport={importProducts} token={token} onStockChange={async (data) => { await request("/inventory/adjustments", token, { method: "POST", body: JSON.stringify(data) }); setToast("Stock adjustment recorded"); refresh(); }} />}
          {page === "Point of sale" && <PointOfSale products={products} categories={categories} token={token} user={user} canDiscount={admin || user.permissions?.apply_discounts} onSale={createSale} onRazorpaySale={completeRazorpaySale} />}
          {page === "Sales" && <Sales sales={sales} token={token} canReturn={admin || user.permissions?.process_returns} onChanged={refresh} onOpen={async (sale) => { try { setLastSale(await request(`/sales/${sale.id}`, token)); setModal("receipt-view"); } catch (err) { setToast(err.message); } }} />}
          {page === "Team" && admin && <Team staff={staff} onAdd={() => setModal("staff")} onEdit={(member) => { setEditingProduct(member); setModal("staff-permissions"); }} />}
          {page === "Purchases" && (admin || user.permissions?.receive_stock) && <Purchases token={token} products={products} canViewCosts={admin || user.permissions?.view_purchase_costs} onChanged={refresh} />}
          {page === "Suppliers" && (admin || user.permissions?.receive_stock) && <Suppliers token={token} canViewCosts={admin || user.permissions?.view_purchase_costs} />}
          {page === "Expenses" && admin && <Expenses token={token} />}
          {page === "Reports" && admin && <Reports token={token} />}
        </>}
      </div>
    </main>
    {modal === "product" && <Modal title={editingProduct ? "Edit product" : "Add a product"} subtitle="Keep your shelves and inventory in sync." onClose={() => setModal("")}><ProductForm product={editingProduct} onSave={saveProduct} onClose={() => setModal("")} canViewCosts={admin || user.permissions?.view_purchase_costs} /></Modal>}
    {modal === "staff" && <Modal title="Add a team member" subtitle="Give your people access to ring up sales." onClose={() => setModal("")}><StaffForm onSave={addStaff} onClose={() => setModal("")} /></Modal>}
    {modal === "staff-permissions" && editingProduct && <Modal title={`Permissions · ${editingProduct.name}`} subtitle="Give this team member access to specific shop tasks." onClose={() => setModal("")}><PermissionsForm staff={editingProduct} onSave={(permissions) => updateStaffPermissions(editingProduct, permissions)} onClose={() => setModal("")} /></Modal>}
    {(modal === "receipt" || modal === "receipt-view") && lastSale && <Receipt sale={lastSale} user={user} store={user.store_name} onClose={() => setModal("")} />}
    {toast && <div className="toast"><span><Check size={15} /></span>{toast}<button onClick={() => setToast("")}><X size={15} /></button></div>}
  </div>;
}

function Overview({ dashboard, user, onNavigate, sales }) {
  const chart = dashboard?.chart || [];
  const max = Math.max(1, ...chart.map((day) => day.revenue));
  const [range, setRange] = useState("Last 7 days");
  const recent = dashboard?.recent_sales || [];
  return <div className="page-wrap">
    <div className="page-heading"><div><span className="eyebrow">{new Date().toLocaleDateString([], { weekday: "long", month: "long", day: "numeric" }).toUpperCase()}</span><h1>Good morning, {user.name.split(" ")[0]} <span className="wave">✳</span></h1><p>Here's what's happening at {user.store_name} today.</p></div><button className="button button-primary" onClick={() => onNavigate("Point of sale")}><Plus size={17} /> New sale</button></div>
    <section className="stats-grid">
      <StatCard title="Today's revenue" value={money(dashboard?.today_revenue)} foot="Across today's sales" icon={CircleDollarSign} tint="sage" trend="+12.8%" />
      <StatCard title="Orders today" value={dashboard?.today_orders ?? 0} foot="vs. 18 this time last week" icon={ShoppingBag} tint="peach" trend="+4" />
      <StatCard title="Products in stock" value={dashboard?.product_count ?? 0} foot="Across your whole catalog" icon={Package} tint="lavender" />
      <StatCard title="Running low" value={dashboard?.low_stock ?? 0} foot="Items at or below reorder point" icon={AlertTriangle} tint="yellow" />
    </section>
    <section className="overview-grid">
      <article className="surface chart-card"><div className="surface-heading"><div><span className="eyebrow">A LITTLE MOMENTUM</span><h2>Sales overview</h2></div><select className="select-quiet" value={range} onChange={(event) => setRange(event.target.value)}><option>Last 7 days</option></select></div>
        <div className="chart-summary"><b>{money(dashboard?.week_revenue)}</b><span><ArrowUpRight size={14} /> vs. previous week</span></div>
        <div className="chart-area"><div className="chart-y"><span>$1k</span><span>$750</span><span>$500</span><span>$250</span><span>$0</span></div><div className="chart-columns">{chart.map((day) => <div className="chart-column" key={day.date}><div className="bar-rail"><div className={`bar ${day.revenue === max && max > 0 ? "bar-highlight" : ""}`} style={{ height: `${Math.max(day.revenue ? 8 : 2, (day.revenue / max) * 100)}%` }} title={money(day.revenue)} /></div><span>{day.day}</span></div>)}</div></div>
      </article>
      <article className="surface quick-card"><div className="surface-heading"><div><span className="eyebrow">YOUR SHORTCUTS</span><h2>Make it happen</h2></div><span className="quick-spark">✳</span></div>
        <button className="quick-link" onClick={() => onNavigate("Point of sale")}><span className="quick-link-icon sage"><ShoppingCart size={18} /></span><span><b>Start a sale</b><small>Ring up a customer</small></span><ArrowRight size={16} /></button>
        {user.role === "admin" && <button className="quick-link" onClick={() => onNavigate("Inventory")}><span className="quick-link-icon lavender"><Package size={18} /></span><span><b>Add to inventory</b><small>Grow your product list</small></span><ArrowRight size={16} /></button>}
        <button className="quick-link" onClick={() => onNavigate("Sales")}><span className="quick-link-icon peach"><BarChart3 size={18} /></span><span><b>View sales history</b><small>See how you're doing</small></span><ArrowRight size={16} /></button>
      </article>
    </section>
    <section className="surface recent-card"><div className="surface-heading"><div><span className="eyebrow">THE LATEST</span><h2>Recent sales</h2></div><button className="button button-quiet button-sm" onClick={() => onNavigate("Sales")}>See all sales <ArrowRight size={15} /></button></div>
      {recent.length ? <div className="table-wrap"><table><thead><tr><th>RECEIPT</th><th>WHEN</th><th>ITEMS</th><th>TEAM MEMBER</th><th>PAYMENT</th><th className="align-right">TOTAL</th></tr></thead><tbody>{recent.map((sale) => <tr key={sale.id}><td><span className="receipt-id">#{String(sale.id).padStart(5, "0")}</span></td><td>{dateTime(sale.created_at)}</td><td>{sale.item_count} items</td><td><span className="cashier-cell"><span className="mini-avatar">{sale.cashier?.split(" ").map((part) => part[0]).join("").slice(0, 2)}</span>{sale.cashier}</span></td><td><span className="payment-tag">{sale.payment_method}</span></td><td className="align-right amount">{money(sale.total)}</td></tr>)}</tbody></table></div> : <Empty icon={ShoppingBag} title="Your first sale is waiting" body="Once you make a sale, the good stuff shows up here." />}
    </section>
  </div>;
}

function Empty({ icon: Icon, title, body }) {
  return <div className="empty-state"><span><Icon size={22} /></span><b>{title}</b><p>{body}</p></div>;
}

function Inventory({ products, categories, category, setCategory, search, setSearch, lowOnly, setLowOnly, admin, canManage, onAdd, onEdit, onDelete, onImport, onStockChange }) {
  const [page, setPage] = useState(1);
  const [adjustProduct, setAdjustProduct] = useState(null);
  const [adjustment, setAdjustment] = useState({ quantity: "", reason: "" });
  const pageSize = 8;
  useEffect(() => setPage(1), [search, category, lowOnly]);
  const pages = Math.max(1, Math.ceil(products.length / pageSize));
  const slice = products.slice((page - 1) * pageSize, page * pageSize);
  return <div className="page-wrap">
    <div className="page-heading"><div><span className="eyebrow">THE BACK ROOM</span><h1>Inventory</h1><p>A little order goes a long way. Keep your shelves in step.</p></div><div className="inventory-actions"><button className="button button-quiet" disabled={!products.length} onClick={() => { try { printProductLabels(products); } catch (error) { window.alert(error.message); } }}><Barcode size={15} /> Print {products.length} labels</button>{canManage && <><label className="button button-quiet"><FileSpreadsheet size={15} /> Import CSV / Excel<input className="visually-hidden" type="file" accept=".csv,.xlsx" onChange={async (event) => { const file = event.target.files?.[0]; if (file) { try { await onImport(file); } catch (error) { window.alert(error.message); } event.target.value = ""; } }} /></label><button className="button button-primary" onClick={onAdd}><Plus size={17} /> Add product</button></>}</div></div>
    <section className="surface inventory-surface"><div className="inventory-toolbar"><div className="search-box"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Find a product or scan a barcode..." /></div><button className={`button ${lowOnly ? "button-filter-active" : "button-quiet"}`} onClick={() => setLowOnly(!lowOnly)}><AlertTriangle size={15} /> Low stock{lowOnly && <Check size={14} />}</button><span className="result-count">{products.length} {products.length === 1 ? "item" : "items"}</span></div>
      <div className="category-tabs"><button className={category === "All" ? "selected" : ""} onClick={() => setCategory("All")}>All products</button>{categories.map((item) => <button key={item} className={category === item ? "selected" : ""} onClick={() => setCategory(item)}>{item}</button>)}</div>
      {slice.length ? <div className="table-wrap"><table className="inventory-table"><thead><tr><th>PRODUCT</th><th>BARCODE / SKU</th><th>CATEGORY</th><th>IN STOCK</th><th>UNIT PRICE</th><th className="align-right">ACTIONS</th></tr></thead><tbody>{slice.map((product) => <tr key={product.id}><td><div className="product-name-cell"><span className={`product-dot dot-${product.id % 5}`}><Package size={16} /></span><span><b>{product.name}</b><small>{[product.size, product.color].filter(Boolean).join(" · ") || `${product.stock} ${product.unit || "each"} in stock`}</small></span></div></td><td><span className="sku-cell">{product.sku}</span></td><td><span className="category-pill">{product.category}</span></td><td><span className={`stock-label ${product.stock <= product.reorder_level ? "stock-low" : ""}`}>{product.stock <= product.reorder_level && <i />}{product.stock} {product.unit || "each"}{product.stock <= product.reorder_level && <small> · reorder</small>}</span></td><td className="amount">{money(product.price)}</td><td><div className="row-actions"><button className="icon-button" title="Print barcode label" onClick={() => { try { printProductLabel(product); } catch (error) { window.alert(error.message); } }}><Barcode size={16} /></button>{canManage && <><button className="icon-button" title="Adjust stock" onClick={() => { setAdjustProduct(product); setAdjustment({ quantity: "", reason: "" }); }}><Plus size={16} /></button><button className="icon-button" title="Edit product" onClick={() => onEdit(product)}><Settings2 size={16} /></button><button className="icon-button danger-icon" title="Delete product" onClick={() => onDelete(product)}><Trash2 size={16} /></button></>}</div></td></tr>)}</tbody></table></div> : <Empty icon={Package} title="No products found" body="Try another search, or add something new to the shelves." />}
      <footer className="pagination"><span>Showing <b>{products.length ? (page - 1) * pageSize + 1 : 0}–{Math.min(page * pageSize, products.length)}</b> of <b>{products.length}</b> products</span><div><button className="icon-button" disabled={page <= 1} onClick={() => setPage(page - 1)}><ChevronLeft size={17} /></button><span className="page-number">{page} of {pages}</span><button className="icon-button" disabled={page >= pages} onClick={() => setPage(page + 1)}><ChevronRight size={17} /></button></div></footer>
    </section>
    {adjustProduct && <Modal title={`Adjust ${adjustProduct.name}`} subtitle="Record a counted, damaged, or missing stock adjustment." onClose={() => setAdjustProduct(null)}><form className="modal-form" onSubmit={async (event) => { event.preventDefault(); try { await onStockChange({ product_id: adjustProduct.id, quantity: Number(adjustment.quantity), reason: adjustment.reason }); setAdjustProduct(null); } catch (error) { window.alert(error.message); } }}><div className="form-stack"><label>Quantity change<input type="number" required step="1" value={adjustment.quantity} onChange={(event) => setAdjustment({ ...adjustment, quantity: event.target.value })} placeholder="Positive to add, negative to remove" /></label><label>Reason<input required minLength="2" value={adjustment.reason} onChange={(event) => setAdjustment({ ...adjustment, reason: event.target.value })} placeholder="e.g. Damaged goods, stock count" /></label></div><footer className="modal-actions"><button type="button" className="button button-quiet" onClick={() => setAdjustProduct(null)}>Cancel</button><button className="button button-primary">Record adjustment</button></footer></form></Modal>}
  </div>;
}

function PointOfSale({ products, categories, token, user, canDiscount, onSale, onRazorpaySale }) {
  const [cart, setCart] = useState([]);
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");
  const [discount, setDiscount] = useState("");
  const [payment, setPayment] = useState("card");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [register, setRegister] = useState(undefined);
  const [registerModal, setRegisterModal] = useState("");
  const [cashInput, setCashInput] = useState("");
  const [registerSummary, setRegisterSummary] = useState(null);
  const [razorpayConfig, setRazorpayConfig] = useState(null);
  const [pendingRazorpay, setPendingRazorpay] = useState(null);
  const searchRef = useRef(null);
  useEffect(() => {
    request("/register/current", token).then((session) => {
      setRegister(session);
      if (!session) setRegisterModal("open");
    }).catch((err) => setError(err.message));
    request("/payments/razorpay/config", token).then(setRazorpayConfig).catch(() => setRazorpayConfig({ configured: false }));
  }, [token]);
  const shown = products.filter((product) => product.stock > 0 && (activeCategory === "All" || product.category === activeCategory) && (!search || `${product.name} ${product.brand} ${product.sku}`.toLowerCase().includes(search.toLowerCase())));
  const subtotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const discountAmount = Math.min(subtotal, Math.max(0, Number(discount) || 0));
  const preDiscountTax = cart.reduce((sum, item) => sum + item.price * item.quantity * (Number(item.tax_rate || 0) / 100), 0);
  const taxTotal = subtotal ? Math.round(preDiscountTax * (subtotal - discountAmount) / subtotal * 100) / 100 : 0;
  function add(product) {
    setError("");
    setCart((current) => {
      const existing = current.find((item) => item.id === product.id);
      if (existing) return current.map((item) => item.id === product.id ? { ...item, quantity: Math.min(item.stock, item.quantity + 1) } : item);
      return [...current, { ...product, quantity: 1 }];
    });
  }
  function scan(event) {
    event.preventDefault();
    const found = products.find((product) => product.sku.toLowerCase() === search.trim().toLowerCase());
    if (found && found.stock > 0) { add(found); setSearch(""); } else if (search.trim()) setError("No in-stock product found for that barcode.");
  }
  function quantity(id, value) {
    setCart((current) => current.map((item) => item.id === id ? { ...item, quantity: Math.min(item.stock, item.quantity + value) } : item).filter((item) => item.quantity > 0));
  }
  function setItemQuantity(id, value) {
    const parsed = Number(value);
    setCart((current) => current.map((item) => item.id === id ? { ...item, quantity: Math.min(item.stock, parsed) } : item).filter((item) => item.quantity > 0));
  }
  async function checkout() {
    if (!cart.length || !register) return;
    setBusy(true); setError("");
    try {
      if (pendingRazorpay) {
        const result = await request("/payments/razorpay/verify", token, { method: "POST", body: JSON.stringify(pendingRazorpay) });
        setPendingRazorpay(null); setCart([]); setDiscount(""); onRazorpaySale(result.sale);
        return;
      }
      if (payment === "razorpay") {
        if (!razorpayConfig?.configured) throw new Error("Razorpay isn't configured for this store yet.");
        const order = await request("/payments/razorpay/orders", token, {
          method: "POST",
          body: JSON.stringify({ items: cart.map((item) => ({ product_id: item.id, quantity: item.quantity })), discount: discountAmount }),
        });
        if (!window.Razorpay) throw new Error("Razorpay Checkout couldn't load. Check your connection and retry.");
        const checkout = new window.Razorpay({
          key: order.key_id,
          amount: order.amount,
          currency: order.currency,
          name: order.name || "Counterpoint",
          description: order.description,
          order_id: order.order_id,
          prefill: { name: user.name, email: user.email },
          theme: { color: "#315f4c" },
          handler: async (response) => {
            const paymentDetails = {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            };
            setPendingRazorpay(paymentDetails); setBusy(true); setError("");
            try {
              const result = await request("/payments/razorpay/verify", token, { method: "POST", body: JSON.stringify(paymentDetails) });
              setPendingRazorpay(null); setCart([]); setDiscount(""); onRazorpaySale(result.sale);
            } catch (err) { setError(`${err.message} Payment details are saved; use “Retry payment confirmation” before starting another charge.`); }
            finally { setBusy(false); }
          },
          modal: { ondismiss: () => setBusy(false) },
        });
        checkout.on("payment.failed", (failure) => {
          setError(failure.error?.description || "Razorpay couldn't complete this payment.");
          setBusy(false);
        });
        checkout.open();
        setBusy(false);
        return;
      }
      await onSale({ items: cart.map((item) => ({ product_id: item.id, quantity: item.quantity })), discount: discountAmount, payment_method: payment });
      setCart([]); setDiscount("");
    }
    catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  async function openRegister(event) {
    event.preventDefault();
    try {
      const session = await request("/register/open", token, { method: "POST", body: JSON.stringify({ opening_cash: Number(cashInput || 0) }) });
      setRegister(session); setRegisterModal(""); setCashInput(""); setError("");
    } catch (err) { setError(err.message); }
  }
  async function closeRegister(event) {
    event.preventDefault();
    try {
      const summary = await request("/register/close", token, { method: "POST", body: JSON.stringify({ counted_cash: Number(cashInput || 0) }) });
      setRegisterSummary(summary); setRegister(null); setRegisterModal(""); setCart([]); setDiscount(""); setCashInput("");
    } catch (err) { setError(err.message); }
  }
  return <div className="page-wrap pos-page"><div className="page-heading pos-heading"><div><span className="eyebrow">A FRIENDLY HELLO, A HAPPY GOODBYE</span><h1>Point of sale</h1><p>Ring 'em up. You're right where you need to be.</p></div><button className={`register-status ${register ? "register-open" : "register-closed"}`} onClick={() => { setError(""); setCashInput(""); setRegisterModal(register ? "close" : "open"); }}><i /> {register ? "Shift open · Close" : "Open register"}</button></div>
    {registerSummary && <div className="register-summary"><b>Shift closed.</b><span>Expected cash {money(registerSummary.expected_cash)} · Counted {money(registerSummary.counted_cash)} · Difference {money(registerSummary.difference)}</span><button className="icon-button" onClick={() => setRegisterSummary(null)}><X size={14} /></button></div>}
    <div className="pos-layout"><section className="pos-catalog"><form className="search-box pos-search" onSubmit={scan}><Barcode size={18} /><input ref={searchRef} autoFocus value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Scan a barcode or find a product..." /><kbd>ENTER</kbd></form>
      <div className="category-tabs pos-tabs"><button className={activeCategory === "All" ? "selected" : ""} onClick={() => setActiveCategory("All")}>Everything</button>{categories.map((item) => <button key={item} className={activeCategory === item ? "selected" : ""} onClick={() => setActiveCategory(item)}>{item}</button>)}</div>
      <div className="pos-product-grid">{shown.map((product) => <button className="pos-product" key={product.id} onClick={() => add(product)}><span className={`pos-product-art art-${product.id % 6}`}><Package size={23} /><i><Plus size={13} /></i></span><span className="pos-product-name">{product.name}</span><span className="pos-product-detail"><b>{money(product.price)}</b><small>{product.stock} in stock</small></span></button>)}</div>
      {!shown.length && <Empty icon={Search} title="Nothing on this shelf" body="Try a different search or category." />}
    </section>
    <aside className="cart-panel"><div className="cart-heading"><div><span className="eyebrow">CHECKOUT</span><h2>Current sale</h2></div><span className="cart-count">{cart.reduce((n, item) => n + item.quantity, 0)} items</span></div>
      {!cart.length ? <div className="cart-empty"><span><ShoppingCart size={21} /></span><b>Room for something good</b><p>Scan a barcode or tap any product to start a sale.</p></div> : <div className="cart-lines">{cart.map((item) => <div className="cart-line" key={item.id}><span className={`cart-product-thumb art-${item.id % 6}`}><Package size={16} /></span><div className="cart-product-info"><b>{item.name}{item.size ? ` · ${item.size}` : ""}{item.color ? ` · ${item.color}` : ""}</b><small>{money(item.price)} per {item.unit || "each"}</small><div className="quantity-control"><button onClick={() => quantity(item.id, -(item.unit === "each" ? 1 : 0.1))}><Minus size={12} /></button><input aria-label={`Quantity of ${item.name}`} type="number" min="0.001" max={item.stock} step={item.unit === "each" ? "1" : "0.001"} value={item.quantity} onChange={(event) => setItemQuantity(item.id, event.target.value)} /><button disabled={item.quantity >= item.stock} onClick={() => quantity(item.id, item.unit === "each" ? 1 : 0.1)}><Plus size={12} /></button></div></div><div className="cart-line-total"><b>{money(item.price * item.quantity)}</b><button title="Remove item" onClick={() => setCart(cart.filter((entry) => entry.id !== item.id))}><X size={14} /></button></div></div>)}</div>}
      <div className="cart-bottom">{canDiscount && <label className="discount-field"><span><Tag size={15} /> Little discount</span><span className="discount-input-wrap"><span>{new Intl.NumberFormat("en-US", { style: "currency", currency: localStorage.getItem("counterpoint_currency") || "INR" }).formatToParts(0).find((part) => part.type === "currency")?.value}</span><input type="number" min="0" max={subtotal} step="0.01" value={discount} onChange={(event) => setDiscount(event.target.value)} placeholder="0.00" /></span></label>}
        <div className="cart-totals"><div><span>Subtotal</span><b>{money(subtotal)}</b></div>{discountAmount > 0 && <div className="discount-row"><span>Discount</span><b>-{money(discountAmount)}</b></div>}{taxTotal > 0 && <div><span>Tax</span><b>{money(taxTotal)}</b></div>}<div className="cart-grand"><span>Total due</span><b>{money(subtotal - discountAmount + taxTotal)}</b></div></div>
        <div className="payment-options"><span>Payment</span><div><button className={payment === "card" ? "selected" : ""} onClick={() => setPayment("card")}><CreditCard size={15} /> Card</button><button className={payment === "cash" ? "selected" : ""} onClick={() => setPayment("cash")}><CircleDollarSign size={15} /> Cash</button><button className={payment === "upi" ? "selected" : ""} onClick={() => setPayment("upi")}><MoreIcon /> UPI</button><button disabled={!razorpayConfig?.configured} title={razorpayConfig?.configured ? "Pay online with Razorpay" : "Add Razorpay API keys to enable online payments"} className={payment === "razorpay" ? "selected" : ""} onClick={() => setPayment("razorpay")}><CreditCard size={15} /> Online</button></div></div>
        {error && <div className="inline-error">{error}</div>}
        <button disabled={!cart.length || busy || !register} className="button button-primary checkout-button" onClick={checkout}>{busy ? "Finishing up..." : pendingRazorpay ? <>Retry payment confirmation <ArrowRight size={17} /></> : !register ? "Open register to charge" : payment === "razorpay" ? <>Pay online {money(subtotal - discountAmount + taxTotal)} <ArrowRight size={17} /></> : <>Charge {money(subtotal - discountAmount + taxTotal)} <ArrowRight size={17} /></>}</button>
        <div className="secure-note"><ShieldCheck size={14} /> A good day at the register.</div>
      </div>
    </aside></div>
    {registerModal === "open" && <Modal title="Open your register" subtitle="Count the starting cash in your drawer before your shift." onClose={() => setRegisterModal("")}><form className="modal-form" onSubmit={openRegister}><div className="form-stack"><label>Opening cash<input type="number" min="0" step="0.01" required value={cashInput} onChange={(event) => setCashInput(event.target.value)} placeholder="0.00" /></label><p className="field-hint">Cash sales, cash refunds and payment totals will be reconciled against this shift.</p></div>{error && <div className="inline-error">{error}</div>}<footer className="modal-actions"><button type="button" className="button button-quiet" onClick={() => setRegisterModal("")}>Later</button><button className="button button-primary">Open shift</button></footer></form></Modal>}
    {registerModal === "close" && <Modal title="Close your register" subtitle="Count the cash in the drawer; card and UPI totals are reconciled separately." onClose={() => setRegisterModal("")}><form className="modal-form" onSubmit={closeRegister}><div className="register-close-summary"><div><span>Opening cash</span><b>{money(register.opening_cash)}</b></div><div><span>Cash sales</span><b>{money(register.cash_sales)}</b></div><div><span>Cash refunds</span><b>-{money(register.cash_refunds)}</b></div><div><span>Expected in drawer</span><b>{money(register.expected_cash)}</b></div><div><span>Card collected</span><b>{money(register.card_sales)}</b></div><div><span>UPI collected</span><b>{money(register.upi_sales)}</b></div></div><label className="register-count-field">Counted cash<input type="number" min="0" step="0.01" required value={cashInput} onChange={(event) => setCashInput(event.target.value)} placeholder="0.00" /></label>{error && <div className="inline-error">{error}</div>}<footer className="modal-actions"><button type="button" className="button button-quiet" onClick={() => setRegisterModal("")}>Keep shift open</button><button disabled={Boolean(cart.length)} className="button button-primary">Close shift</button></footer>{Boolean(cart.length) && <p className="field-hint">Finish or clear the current sale before closing the register.</p>}</form></Modal>}
  </div>;
}

function MoreIcon() { return <CircleDollarSign size={15} />; }

function Sales({ sales, token, onChanged, onOpen }) {
  const [search, setSearch] = useState("");
  const [returnSale, setReturnSale] = useState(null);
  const [returnQuantities, setReturnQuantities] = useState({});
  const [returnError, setReturnError] = useState("");
  const [returnBusy, setReturnBusy] = useState(false);
  const filtered = sales.filter((sale) => `#${sale.id} ${sale.cashier} ${sale.payment_method}`.toLowerCase().includes(search.toLowerCase()));
  const total = sales.reduce((sum, sale) => sum + sale.total, 0);
  async function openReturn(sale) {
    try {
      setReturnSale(await request(`/sales/${sale.id}`, token));
      setReturnQuantities({});
      setReturnError("");
    } catch (err) { setReturnError(err.message); }
  }
  async function submitReturn(event) {
    event.preventDefault(); setReturnBusy(true); setReturnError("");
    const items = returnSale.items.filter((item) => Number(returnQuantities[item.id]?.quantity || 0) > 0)
      .map((item) => ({ sale_item_id: item.id, quantity: Number(returnQuantities[item.id].quantity), restock: returnQuantities[item.id].restock !== false }));
    try {
      if (!items.length) throw new Error("Enter a quantity for at least one item.");
      const result = await request(`/sales/${returnSale.id}/returns`, token, { method: "POST", body: JSON.stringify({ items }) });
      setReturnSale(null); onChanged(); window.alert(`Return recorded. Refund: ${money(result.refund_total)}`);
    } catch (err) { setReturnError(err.message); } finally { setReturnBusy(false); }
  }
  return <div className="page-wrap"><div className="page-heading"><div><span className="eyebrow">THE GOOD WORK</span><h1>Sales</h1><p>Every lovely little transaction, all in one place.</p></div></div>
    <div className="sales-highlights"><div className="sales-highlight"><span className="stat-icon sage"><TrendingUp size={17} /></span><div><small>Gross sales · all time</small><b>{money(total)}</b></div></div><div className="sales-highlight"><span className="stat-icon peach"><ShoppingBag size={17} /></span><div><small>Sales made</small><b>{sales.length}</b></div></div><div className="sales-highlight"><span className="stat-icon lavender"><Tag size={17} /></span><div><small>Discounts given</small><b>{money(sales.reduce((sum, sale) => sum + sale.discount, 0))}</b></div></div></div>
    <section className="surface sales-surface"><div className="inventory-toolbar"><div><span className="eyebrow">YOUR RECEIPT BOOK</span><h2>All sales <span className="count-soft">{sales.length}</span></h2></div><div className="search-box sales-search"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Find a receipt..." /></div></div>
      {filtered.length ? <div className="table-wrap"><table><thead><tr><th>RECEIPT</th><th>DATE & TIME</th><th>CASHIER</th><th>ITEMS</th><th>PAYMENT</th><th className="align-right">TOTAL</th><th></th></tr></thead><tbody>{filtered.map((sale) => <tr key={sale.id}><td><span className="receipt-id">#{String(sale.id).padStart(5, "0")}</span></td><td>{dateTime(sale.created_at)}</td><td><span className="cashier-cell"><span className="mini-avatar">{sale.cashier?.split(" ").map((part) => part[0]).join("").slice(0, 2)}</span>{sale.cashier}</span></td><td>{sale.item_count} items</td><td><span className="payment-tag">{sale.payment_method}</span></td><td className="align-right amount">{money(sale.total)}</td><td><div className="row-actions"><button className="icon-button" title="View receipt" onClick={() => onOpen(sale)}><Printer size={15} /></button>{canReturn && <button className="icon-button" title="Return items" onClick={() => openReturn(sale)}><RotateCcw size={15} /></button>}</div></td></tr>)}</tbody></table></div> : <Empty icon={ClipboardList} title="No receipts just yet" body="Your sales will be waiting here when you need them." />}
    </section>
    {returnSale && <Modal title={`Return receipt #${String(returnSale.id).padStart(5, "0")}`} subtitle="Choose quantities to refund. Restocked items return to inventory." onClose={() => setReturnSale(null)}><form className="modal-form" onSubmit={submitReturn}><div className="return-lines">{returnSale.items.map((item) => <div className="return-line" key={item.id}><div><b>{item.product_name}</b><small>{item.variant || item.sku} · {item.quantity} sold · {money(item.unit_price)} each</small></div><input aria-label={`Return quantity for ${item.product_name}`} type="number" min="0" max={item.quantity} step="1" value={returnQuantities[item.id]?.quantity || ""} onChange={(event) => setReturnQuantities({ ...returnQuantities, [item.id]: { ...returnQuantities[item.id], quantity: event.target.value } })} placeholder="0" /><label><input type="checkbox" checked={returnQuantities[item.id]?.restock !== false} onChange={(event) => setReturnQuantities({ ...returnQuantities, [item.id]: { ...returnQuantities[item.id], restock: event.target.checked } })} /> Restock</label></div>)}</div>{returnError && <div className="inline-error">{returnError}</div>}<footer className="modal-actions"><button type="button" className="button button-quiet" onClick={() => setReturnSale(null)}>Cancel</button><button disabled={returnBusy} className="button button-primary">{returnBusy ? "Recording..." : "Record return"}</button></footer></form></Modal>}
    {returnError && !returnSale && <div className="toast">{returnError}</div>}
  </div>;
}

function Team({ staff, onAdd, onEdit }) {
  return <div className="page-wrap"><div className="page-heading"><div><span className="eyebrow">GOOD PEOPLE, GOOD BUSINESS</span><h1>Your team</h1><p>Everything runs better when everyone has a place.</p></div><button className="button button-primary" onClick={onAdd}><Plus size={17} /> Add team member</button></div>
    <div className="team-summary"><span className="team-summary-icon"><Users size={20} /></span><span><b>{staff.length} {staff.length === 1 ? "person" : "people"}</b><small>have a place at your counter</small></span></div>
    <section className="surface team-surface"><div className="team-grid">{staff.map((person, index) => <article className="team-card" key={person.id}><div className={`team-avatar team-avatar-${index % 4}`}>{person.name.split(" ").map((part) => part[0]).join("").slice(0, 2)}</div><div className="team-person"><b>{person.name}</b><span>{person.email}</span></div><span className={`role-pill ${person.role}`}>{person.role === "admin" ? <ShieldCheck size={13} /> : <UserRound size={13} />}{person.role}</span>{person.role === "staff" && <button className="button button-quiet button-sm" onClick={() => onEdit(person)}>Permissions</button>}<span className="team-since">Joined {new Date(person.created_at).toLocaleDateString([], { month: "short", year: "numeric" })}</span></article>)}</div>
      <div className="role-note"><ShieldCheck size={17} /><p><b>Different people, different permissions.</b> Admins can manage inventory and the team. Staff can process sales and print receipts.</p></div>
    </section>
  </div>;
}

function Purchases({ token, products, canViewCosts, onChanged }) {
  const [suppliers, setSuppliers] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [supplierModal, setSupplierModal] = useState(false);
  const [form, setForm] = useState({ supplier_id: "", invoice_number: "", invoice_date: new Date().toISOString().slice(0, 10), freight: "", paid_amount: "" });
  const [lines, setLines] = useState([{ product_id: "", quantity: "1", unit_cost: "", tax_rate: "0", batch_number: "", expiry_date: "" }]);
  const reload = useCallback(async () => {
    const [suppliersResult, purchasesResult] = await Promise.all([request("/suppliers", token), request("/purchases", token)]);
    setSuppliers(suppliersResult); setPurchases(purchasesResult);
  }, [token]);
  useEffect(() => { reload().catch((err) => setError(err.message)); }, [reload]);
  function updateLine(index, key, value) {
    setLines((current) => current.map((line, row) => row === index ? { ...line, [key]: value } : line));
  }
  async function submitPurchase(event) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      await request("/purchases", token, { method: "POST", body: JSON.stringify({
        ...form, supplier_id: Number(form.supplier_id), freight: Number(form.freight || 0), paid_amount: Number(form.paid_amount || 0),
        items: lines.map((line) => ({ product_id: Number(line.product_id), quantity: Number(line.quantity), unit_cost: Number(line.unit_cost), tax_rate: Number(line.tax_rate || 0), batch_number: line.batch_number, expiry_date: line.expiry_date })),
      }) });
      setForm({ ...form, invoice_number: "", freight: "", paid_amount: "" }); setLines([{ product_id: "", quantity: "1", unit_cost: "", tax_rate: "0", batch_number: "", expiry_date: "" }]);
      await reload(); onChanged(); setError("");
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  async function saveSupplier(data) {
    const supplier = await request("/suppliers", token, { method: "POST", body: JSON.stringify(data) });
    await reload(); setForm((current) => ({ ...current, supplier_id: String(supplier.id) }));
  }
  const invoiceTotal = lines.reduce((sum, line) => sum + (Number(line.quantity || 0) * Number(line.unit_cost || 0) * (1 + Number(line.tax_rate || 0) / 100)), 0) + Number(form.freight || 0);
  return <div className="page-wrap">
    <div className="page-heading"><div><span className="eyebrow">SUPPLY & RECEIVE</span><h1>Purchases</h1><p>Record supplier invoices once; stock and landed costs update automatically.</p></div><button className="button button-quiet" onClick={() => setSupplierModal(true)}><Plus size={15} /> New supplier</button></div>
    <section className="surface purchase-entry"><div className="surface-heading"><div><span className="eyebrow">GOODS RECEIPT</span><h2>Record an invoice</h2></div><span className="category-pill">Receiving updates stock</span></div>
      <form onSubmit={submitPurchase}><div className="form-grid purchase-header-fields"><label>Supplier<select required value={form.supplier_id} onChange={(event) => setForm({ ...form, supplier_id: event.target.value })}><option value="">Choose supplier</option>{suppliers.map((supplier) => <option value={supplier.id} key={supplier.id}>{supplier.name}</option>)}</select></label><label>Invoice number<input required value={form.invoice_number} onChange={(event) => setForm({ ...form, invoice_number: event.target.value })} placeholder="INV-1048" /></label><label>Invoice date<input type="date" required value={form.invoice_date} onChange={(event) => setForm({ ...form, invoice_date: event.target.value })} /></label></div>
        <div className="purchase-lines-head"><span>PRODUCT</span><span>QUANTITY</span><span>UNIT COST</span><span>TAX %</span><span></span></div>
        {lines.map((line, index) => <div className="purchase-line-wrap" key={index}><div className="purchase-line"><select required value={line.product_id} onChange={(event) => updateLine(index, "product_id", event.target.value)}><option value="">Select item</option>{products.map((product) => <option value={product.id} key={product.id}>{product.name}{product.size ? ` · ${product.size}` : ""} ({product.sku})</option>)}</select><input required type="number" min="0.001" step="0.001" value={line.quantity} onChange={(event) => updateLine(index, "quantity", event.target.value)} /><input required type="number" min="0" step="0.01" value={line.unit_cost} onChange={(event) => updateLine(index, "unit_cost", event.target.value)} placeholder="0.00" /><input type="number" min="0" max="100" step="0.01" value={line.tax_rate} onChange={(event) => updateLine(index, "tax_rate", event.target.value)} /><button type="button" className="icon-button" disabled={lines.length === 1} onClick={() => setLines(lines.filter((_, row) => row !== index))}><Trash2 size={15} /></button></div><div className="purchase-batch-fields"><input value={line.batch_number} onChange={(event) => updateLine(index, "batch_number", event.target.value)} placeholder="Batch / lot (optional)" /><input type="date" value={line.expiry_date} onChange={(event) => updateLine(index, "expiry_date", event.target.value)} aria-label="Batch expiry date" /></div></div>)}
        <button type="button" className="text-button add-line" onClick={() => setLines([...lines, { product_id: "", quantity: "1", unit_cost: "", tax_rate: "0", batch_number: "", expiry_date: "" }])}><Plus size={14} /> Add invoice item</button>
        <div className="purchase-footer"><label>Freight<input type="number" min="0" step="0.01" value={form.freight} onChange={(event) => setForm({ ...form, freight: event.target.value })} placeholder="0.00" /></label><label>Paid now<input type="number" min="0" step="0.01" value={form.paid_amount} onChange={(event) => setForm({ ...form, paid_amount: event.target.value })} placeholder="0.00" /></label><div className="purchase-total"><small>Estimated invoice total</small><b>{money(invoiceTotal)}</b></div><button disabled={busy || !suppliers.length || !products.length} className="button button-primary">{busy ? "Receiving..." : "Receive stock"}</button></div>
        {error && <div className="inline-error">{error}</div>}
      </form>
    </section>
    <section className="surface recent-card purchase-history"><div className="surface-heading"><div><span className="eyebrow">SUPPLIER INVOICES</span><h2>Recent purchases</h2></div></div>
      {purchases.length ? <div className="table-wrap"><table><thead><tr><th>INVOICE</th><th>SUPPLIER</th><th>DATE</th>{canViewCosts && <><th>PAID</th><th className="align-right">TOTAL</th><th className="align-right">OUTSTANDING</th></>}</tr></thead><tbody>{purchases.map((purchase) => <tr key={purchase.id}><td className="receipt-id">{purchase.invoice_number}</td><td>{purchase.supplier_name}</td><td>{purchase.invoice_date}</td>{canViewCosts && <><td>{money(purchase.paid_amount)}</td><td className="align-right amount">{money(purchase.total)}</td><td className="align-right">{money(purchase.total - purchase.paid_amount)}</td></>}</tr>)}</tbody></table></div> : <Empty icon={Truck} title="No purchase invoices yet" body="Record a supplier invoice above to receive stock." />}
    </section>
    {supplierModal && <Modal title="Add supplier" subtitle="Add the supplier for the incoming invoice." onClose={() => setSupplierModal(false)}><SupplierForm token={token} onSave={saveSupplier} onClose={() => setSupplierModal(false)} /></Modal>}
  </div>;
}

function SupplierForm({ token, onSave, onClose }) {
  const [form, setForm] = useState({ name: "", contact_name: "", email: "", phone: "", address: "" });
  const [error, setError] = useState("");
  async function submit(event) {
    event.preventDefault(); setError("");
    try { await onSave(form); onClose(); } catch (err) { setError(err.message); }
  }
  const change = (key) => (event) => setForm({ ...form, [key]: event.target.value });
  return <form className="modal-form" onSubmit={submit}><div className="form-stack"><label>Supplier / business name<input required minLength="2" value={form.name} onChange={change("name")} /></label><label>Contact person<input value={form.contact_name} onChange={change("contact_name")} /></label><label>Email<input type="email" value={form.email} onChange={change("email")} /></label><label>Phone<input value={form.phone} onChange={change("phone")} /></label><label>Address<input value={form.address} onChange={change("address")} /></label></div>{error && <div className="inline-error">{error}</div>}<footer className="modal-actions"><button type="button" className="button button-quiet" onClick={onClose}>Cancel</button><button className="button button-primary">Save supplier</button></footer></form>;
}

function Suppliers({ token, canViewCosts }) {
  const [suppliers, setSuppliers] = useState([]);
  const [error, setError] = useState("");
  const [modal, setModal] = useState(false);
  const reload = useCallback(() => request("/suppliers", token).then(setSuppliers), [token]);
  useEffect(() => { reload().catch((err) => setError(err.message)); }, [reload]);
  async function save(data) { await request("/suppliers", token, { method: "POST", body: JSON.stringify(data) }); await reload(); }
  return <div className="page-wrap"><div className="page-heading"><div><span className="eyebrow">YOUR SUPPLY PARTNERS</span><h1>Suppliers</h1><p>Keep supplier contacts, invoices and balances in one place.</p></div><button className="button button-primary" onClick={() => setModal(true)}><Plus size={16} /> Add supplier</button></div>
    <section className="surface recent-card">{error && <div className="inline-error">{error}</div>}{suppliers.length ? <div className="table-wrap"><table><thead><tr><th>SUPPLIER</th><th>CONTACT</th><th>EMAIL</th><th>PHONE</th>{canViewCosts && <><th>INVOICES</th><th className="align-right">BALANCE DUE</th></>}</tr></thead><tbody>{suppliers.map((supplier) => <tr key={supplier.id}><td><b>{supplier.name}</b></td><td>{supplier.contact_name || "—"}</td><td>{supplier.email || "—"}</td><td>{supplier.phone || "—"}</td>{canViewCosts && <><td>{supplier.invoice_count}</td><td className="align-right amount">{money(supplier.outstanding)}</td></>}</tr>)}</tbody></table></div> : <Empty icon={Users} title="No suppliers added" body="Add your suppliers to keep purchases and balances organized." />}</section>
    {modal && <Modal title="Add supplier" subtitle="Keep the details handy for next time." onClose={() => setModal(false)}><SupplierForm token={token} onSave={save} onClose={() => setModal(false)} /></Modal>}
  </div>;
}

function Expenses({ token }) {
  const [expenses, setExpenses] = useState([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ category: "Rent", description: "", amount: "", expense_date: new Date().toISOString().slice(0, 10) });
  const reload = useCallback(() => request("/expenses", token).then(setExpenses), [token]);
  useEffect(() => { reload().catch((err) => setError(err.message)); }, [reload]);
  async function submit(event) {
    event.preventDefault(); setError("");
    try { await request("/expenses", token, { method: "POST", body: JSON.stringify({ ...form, amount: Number(form.amount) }) }); setForm({ ...form, description: "", amount: "" }); await reload(); }
    catch (err) { setError(err.message); }
  }
  const total = expenses.reduce((sum, expense) => sum + expense.amount, 0);
  return <div className="page-wrap"><div className="page-heading"><div><span className="eyebrow">THE COST OF DOING BUSINESS</span><h1>Expenses</h1><p>Track overhead separately from stock purchases.</p></div><div className="sales-highlight"><span className="stat-icon peach"><Wallet size={17} /></span><div><small>Recorded expenses</small><b>{money(total)}</b></div></div></div>
    <section className="surface expense-entry"><div className="surface-heading"><div><span className="eyebrow">ADD A RECORD</span><h2>New expense</h2></div></div><form className="expense-form" onSubmit={submit}><label>Category<select value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })}><option>Rent</option><option>Payroll</option><option>Utilities</option><option>Supplies</option><option>Marketing</option><option>Other</option></select></label><label>Description<input required value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="Monthly shop rent" /></label><label>Amount<input type="number" min="0.01" step="0.01" required value={form.amount} onChange={(event) => setForm({ ...form, amount: event.target.value })} placeholder="0.00" /></label><label>Date<input type="date" required value={form.expense_date} onChange={(event) => setForm({ ...form, expense_date: event.target.value })} /></label><button className="button button-primary"><Plus size={15} /> Record expense</button></form>{error && <div className="inline-error">{error}</div>}</section>
    <section className="surface recent-card"><div className="surface-heading"><div><span className="eyebrow">EXPENSE LEDGER</span><h2>Recent expenses</h2></div></div>{expenses.length ? <div className="table-wrap"><table><thead><tr><th>DATE</th><th>CATEGORY</th><th>DESCRIPTION</th><th className="align-right">AMOUNT</th></tr></thead><tbody>{expenses.map((expense) => <tr key={expense.id}><td>{expense.expense_date}</td><td><span className="category-pill">{expense.category}</span></td><td>{expense.description}</td><td className="align-right amount">{money(expense.amount)}</td></tr>)}</tbody></table></div> : <Empty icon={Wallet} title="No expenses recorded" body="Add an expense to include it in your operating profit estimate." />}</section>
  </div>;
}

function localDateInput(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function downloadReportCsv(report, startDate, endDate) {
  const headers = ["section", "period", "product", "sku", "payment_method", "orders", "units", "gross_sales", "discounts", "net_sales", "tax", "refunds", "cost_of_goods", "expenses", "operating_profit", "receipts", "total"];
  const rows = [];
  for (const month of report.months || []) rows.push({ section: "Profit and loss", period: month.month, gross_sales: month.gross_sales, discounts: month.discounts, net_sales: month.net_sales, tax: month.tax_collected, refunds: month.refunds, cost_of_goods: month.cost_of_goods, expenses: month.expenses, operating_profit: month.operating_profit, receipts: month.receipts });
  for (const day of report.daily || []) rows.push({ section: "Daily sales", period: day.day, orders: day.orders, net_sales: day.net_sales, receipts: day.receipts });
  for (const payment of report.payments || []) rows.push({ section: "Payment totals", payment_method: payment.payment_method, orders: payment.orders, total: payment.total });
  for (const product of report.best_sellers || []) rows.push({ section: "Top sellers", product: product.product_name, sku: product.sku, units: product.units_sold, net_sales: product.revenue });
  for (const year of report.yearly || []) rows.push({ section: "Yearly totals", period: year.year, net_sales: year.net_sales, tax: year.tax_collected, refunds: year.refunds, cost_of_goods: year.cost_of_goods, expenses: year.expenses, operating_profit: year.operating_profit, receipts: year.receipts });
  for (const purchase of report.purchases || []) rows.push({ section: "Purchases", period: purchase.month, total: purchase.total });
  const escape = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
  const content = [
    `Report period,${escape(startDate)},${escape(endDate)}`,
    headers.map(escape).join(","),
    ...rows.map((row) => headers.map((header) => escape(row[header])).join(",")),
  ].join("\r\n");
  const url = URL.createObjectURL(new Blob(["\uFEFF", content], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `retail-report-${startDate}-to-${endDate}.csv`;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function Reports({ token }) {
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");
  const [dates, setDates] = useState(() => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    return { start: localDateInput(start), end: localDateInput(end) };
  });
  const [appliedDates, setAppliedDates] = useState(dates);
  useEffect(() => {
    let active = true;
    const query = new URLSearchParams({ start_date: appliedDates.start, end_date: appliedDates.end });
    setError("");
    request(`/reports/financial?${query}`, token)
      .then((result) => { if (active) setReport(result); })
      .catch((err) => { if (active) setError(err.message); });
    return () => { active = false; };
  }, [token, appliedDates]);
  const months = report?.months || [];
  const grossProfit = months.reduce((sum, row) => sum + row.gross_profit, 0);
  const operatingProfit = months.reduce((sum, row) => sum + row.operating_profit, 0);
  function applyDates(event) {
    event.preventDefault();
    if (dates.start > dates.end) { setError("Start date must be on or before end date."); return; }
    setAppliedDates({ ...dates });
  }
  return <div className="page-wrap"><div className="page-heading"><div><span className="eyebrow">THE BIGGER PICTURE</span><h1>Reports</h1><p>Choose a reporting period, then export the results for your records.</p></div><button className="button button-primary" disabled={!report} onClick={() => downloadReportCsv(report, appliedDates.start, appliedDates.end)}><Download size={16} /> Download CSV</button></div>
    {error && <div className="error-banner">{error}</div>}
    <form className="surface report-filters" onSubmit={applyDates}><label>From<input type="date" required value={dates.start} onChange={(event) => setDates({ ...dates, start: event.target.value })} /></label><label>To<input type="date" required value={dates.end} onChange={(event) => setDates({ ...dates, end: event.target.value })} /></label><button className="button button-primary"><BarChart3 size={15} /> Apply period</button><span>Sales, returns, expenses and payment totals are filtered to the selected dates.</span></form>
    <section className="stats-grid report-stats"><StatCard title="Inventory valuation" value={money(report?.inventory_value)} foot="Weighted average cost × on-hand stock" icon={Package} tint="sage" /><StatCard title="Gross profit · selected period" value={money(grossProfit)} foot="Net sales less cost of goods sold" icon={TrendingUp} tint="lavender" /><StatCard title="Operating profit · selected period" value={money(operatingProfit)} foot="Gross profit less recorded expenses" icon={CircleDollarSign} tint="peach" /><StatCard title="Months with sales" value={months.length} foot="Purchases and expenses are separate" icon={BarChart3} tint="yellow" /></section>
    <section className="surface recent-card report-section"><div className="surface-heading"><div><span className="eyebrow">MONTH BY MONTH · {appliedDates.start} TO {appliedDates.end}</span><h2>Profit & loss estimate</h2></div></div>{months.length ? <div className="table-wrap"><table><thead><tr><th>MONTH</th><th>NET SALES</th><th>TAX COLLECTED</th><th>REFUNDS</th><th>COGS</th><th>EXPENSES</th><th className="align-right">OPERATING PROFIT</th></tr></thead><tbody>{months.map((month) => <tr key={month.month}><td className="receipt-id">{month.month}</td><td>{money(month.net_sales)}</td><td>{money(month.tax_collected)}</td><td>{money(month.refunds)}</td><td>{money(month.cost_of_goods)}</td><td>{money(month.expenses)}</td><td className="align-right amount">{money(month.operating_profit)}</td></tr>)}</tbody></table></div> : <Empty icon={BarChart3} title="No activity in this period" body="Choose another date range or record sales and expenses." />}<p className="report-disclaimer">Estimates use weighted-average inventory costs at time of sale. Restocked returns reverse COGS. Tax is shown separately from net sales; accounting results may differ.</p></section>
    <section className="report-lower-grid">
      <article className="surface recent-card"><div className="surface-heading"><div><span className="eyebrow">LONGER VIEW</span><h2>Yearly totals</h2></div></div>{report?.yearly?.length ? <div className="table-wrap"><table><thead><tr><th>YEAR</th><th>NET SALES</th><th>COGS</th><th>EXPENSES</th><th className="align-right">OPERATING PROFIT</th></tr></thead><tbody>{report.yearly.map((row) => <tr key={row.year}><td className="receipt-id">{row.year}</td><td>{money(row.net_sales)}</td><td>{money(row.cost_of_goods)}</td><td>{money(row.expenses)}</td><td className="align-right amount">{money(row.operating_profit)}</td></tr>)}</tbody></table></div> : <p className="report-disclaimer">Yearly summaries appear when you have recorded sales.</p>}</article>
      <article className="surface recent-card"><div className="surface-heading"><div><span className="eyebrow">TENDER RECONCILIATION</span><h2>Payment totals</h2></div></div>{report?.payments?.length ? <div className="table-wrap"><table><thead><tr><th>METHOD</th><th>ORDERS</th><th className="align-right">COLLECTED</th></tr></thead><tbody>{report.payments.map((row) => <tr key={row.payment_method}><td><span className="payment-tag">{row.payment_method}</span></td><td>{row.orders}</td><td className="align-right amount">{money(row.total)}</td></tr>)}</tbody></table></div> : <Empty icon={CreditCard} title="No payments to reconcile" body="Payment totals show after your first sale." />}</article>
    </section>
    <section className="surface recent-card report-section"><div className="surface-heading"><div><span className="eyebrow">SELECTED PERIOD</span><h2>Daily sales</h2></div></div>{report?.daily?.length ? <div className="table-wrap"><table><thead><tr><th>DAY</th><th>ORDERS</th><th>NET SALES</th><th className="align-right">RECEIPTS</th></tr></thead><tbody>{report.daily.map((row) => <tr key={row.day}><td>{row.day}</td><td>{row.orders}</td><td>{money(row.net_sales)}</td><td className="align-right amount">{money(row.receipts)}</td></tr>)}</tbody></table></div> : <Empty icon={BarChart3} title="No daily activity yet" body="Daily totals appear here for the selected period." />}</section>
    <section className="surface recent-card report-section"><div className="surface-heading"><div><span className="eyebrow">PRODUCT MOVEMENT</span><h2>Top sellers</h2></div></div>{report?.best_sellers?.length ? <div className="table-wrap"><table><thead><tr><th>PRODUCT</th><th>SKU</th><th>UNITS SOLD</th><th className="align-right">SALES</th></tr></thead><tbody>{report.best_sellers.map((row) => <tr key={row.sku}><td>{row.product_name}</td><td className="sku-cell">{row.sku}</td><td>{row.units_sold}</td><td className="align-right amount">{money(row.revenue)}</td></tr>)}</tbody></table></div> : <Empty icon={ShoppingBag} title="No products sold yet" body="Your best sellers appear after billing." />}</section>
    <section className="surface recent-card report-section"><div className="surface-heading"><div><span className="eyebrow">STOCK TO KEEP AN EYE ON</span><h2>Slow movers · last 90 days</h2></div></div>{report?.slow_movers?.length ? <div className="table-wrap"><table><thead><tr><th>PRODUCT</th><th>SKU</th><th>UNITS SOLD</th><th className="align-right">STOCK ON HAND</th></tr></thead><tbody>{report.slow_movers.map((row) => <tr key={row.sku}><td>{row.name}</td><td className="sku-cell">{row.sku}</td><td>{row.units_sold_90d}</td><td className="align-right">{row.stock} {row.unit}</td></tr>)}</tbody></table></div> : <Empty icon={Package} title="No stock to review" body="Slow-moving stock will show up here." />}</section>
    {report?.inventory_health?.length > 0 && <section className="surface recent-card report-section"><div className="surface-heading"><div><span className="eyebrow">STOCK AGE</span><h2>Ageing inventory</h2></div></div><div className="table-wrap"><table><thead><tr><th>PRODUCT</th><th>SKU</th><th>OLDEST RECEIPT</th><th>STOCK ON HAND</th><th className="align-right">STOCK VALUE</th></tr></thead><tbody>{report.inventory_health.map((row) => <tr key={row.id}><td>{row.name}</td><td className="sku-cell">{row.sku}</td><td>{new Date(row.oldest_stock_at).toLocaleDateString()}</td><td>{row.stock} {row.unit}</td><td className="align-right amount">{money(row.stock * row.cost)}</td></tr>)}</tbody></table></div></section>}
    {report?.expiring_batches?.length > 0 && <section className="surface recent-card report-section"><div className="surface-heading"><div><span className="eyebrow">FRESHNESS CHECK</span><h2>Expiring lots · next 90 days</h2></div></div><div className="table-wrap"><table><thead><tr><th>PRODUCT</th><th>BATCH</th><th>EXPIRES</th><th>UNITS LEFT</th><th className="align-right">STOCK VALUE</th></tr></thead><tbody>{report.expiring_batches.map((row) => <tr key={`${row.product_id}-${row.batch_number}-${row.expiry_date}`}><td>{row.name}</td><td className="sku-cell">{row.batch_number}</td><td>{row.expiry_date}</td><td>{row.quantity_remaining}</td><td className="align-right amount">{money(row.quantity_remaining * row.unit_cost)}</td></tr>)}</tbody></table></div></section>}
  </div>;
}

function PlatformConsole({ token, user, onLogout }) {
  const [stores, setStores] = useState([]);
  const [form, setForm] = useState({ store_name: "", business_type: "general", currency: "INR", owner_name: "", owner_email: "", owner_password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const reload = useCallback(() => request("/platform/stores", token).then(setStores), [token]);
  useEffect(() => { reload().catch((err) => setError(err.message)); }, [reload]);
  async function createStore(event) {
    event.preventDefault();
    setBusy(true); setError(""); setNotice("");
    try {
      const store = await request("/platform/stores", token, {
        method: "POST",
        body: JSON.stringify(form),
      });
      setForm({ store_name: "", business_type: "general", currency: "INR", owner_name: "", owner_email: "", owner_password: "" });
      setNotice(`${store.name} is ready. Give ${store.owner_email} their login details through a secure channel.`);
      await reload();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  async function toggleStore(store) {
    setError(""); setNotice("");
    try {
      await request(`/platform/stores/${store.id}/status?status=${store.status === "active" ? "suspended" : "active"}`, token, { method: "PATCH" });
      setNotice(`${store.name} is now ${store.status === "active" ? "suspended" : "active"}.`);
      await reload();
    } catch (err) { setError(err.message); }
  }
  return <div className="platform-shell">
    <header className="platform-topbar"><a className="brand" href="#"><span className="brand-mark"><Store size={19} /></span><span>counterpoint<small>PLATFORM OWNER</small></span></a><div className="platform-user"><span>{user.email}</span><button className="button button-quiet" onClick={onLogout}><LogOut size={15} /> Sign out</button></div></header>
    <main className="platform-content">
      <div className="page-heading"><div><span className="eyebrow">RETAILER ONBOARDING</span><h1>Shop workspaces</h1><p>Create each retailer's private workspace and issue the owner's login.</p></div><div className="platform-count"><b>{stores.length}</b><span>retailer{stores.length === 1 ? "" : "s"}</span></div></div>
      {error && <div className="error-banner">{error}</div>}
      {notice && <div className="platform-notice"><Check size={17} />{notice}</div>}
      <div className="platform-grid">
        <section className="surface platform-create">
          <div className="surface-heading"><div><span className="eyebrow">NEW RETAILER</span><h2>Create a shop account</h2></div></div>
          <form className="form-stack" onSubmit={createStore}>
            <label>Shop / business name<input required minLength="2" maxLength="100" value={form.store_name} onChange={(event) => setForm({ ...form, store_name: event.target.value })} placeholder="The Corner Market" /></label>
            <div className="form-grid">
              <label>Business type<select value={form.business_type} onChange={(event) => setForm({ ...form, business_type: event.target.value })}><option value="general">General retail</option><option value="supermarket">Supermarket / grocery</option><option value="fashion">Fashion / clothing</option><option value="footwear">Footwear</option><option value="other">Other retail</option></select></label>
              <label>Currency<select value={form.currency} onChange={(event) => setForm({ ...form, currency: event.target.value })}><option value="INR">INR · Indian rupee</option><option value="USD">USD · US dollar</option><option value="EUR">EUR · Euro</option><option value="GBP">GBP · British pound</option><option value="AUD">AUD · Australian dollar</option><option value="CAD">CAD · Canadian dollar</option></select></label>
            </div>
            <label>Shop owner's name<input required minLength="2" maxLength="100" value={form.owner_name} onChange={(event) => setForm({ ...form, owner_name: event.target.value })} placeholder="Alex Morgan" /></label>
            <label>Shop owner's email<input type="email" required value={form.owner_email} onChange={(event) => setForm({ ...form, owner_email: event.target.value })} placeholder="owner@theirshop.com" /></label>
            <label>Initial password<input type="password" required minLength="8" maxLength="128" autoComplete="new-password" value={form.owner_password} onChange={(event) => setForm({ ...form, owner_password: event.target.value })} placeholder="At least 8 characters" /></label>
            <p className="field-hint">Use a unique owner email and share the initial login details with the shop owner privately.</p>
            <button className="button button-primary" disabled={busy}><Plus size={16} />{busy ? "Creating workspace..." : "Create shop workspace"}</button>
          </form>
        </section>
        <section className="surface platform-stores">
          <div className="surface-heading"><div><span className="eyebrow">YOUR CUSTOMERS</span><h2>Retailer accounts</h2></div></div>
          {stores.length ? <div className="table-wrap"><table><thead><tr><th>SHOP</th><th>OWNER</th><th>TYPE</th><th>USERS</th><th>STATUS</th><th></th></tr></thead><tbody>{stores.map((store) => <tr key={store.id}><td><b>{store.name}</b><small className="platform-store-meta">{store.currency} · joined {new Date(store.created_at).toLocaleDateString()}</small></td><td><b>{store.owner_name}</b><small className="platform-store-meta">{store.owner_email}</small></td><td className="platform-capitalize">{store.business_type}</td><td>{store.user_count}</td><td><span className={`platform-status ${store.status}`}>{store.status}</span></td><td><button className="button button-quiet button-sm" onClick={() => toggleStore(store)}>{store.status === "active" ? "Suspend" : "Reactivate"}</button></td></tr>)}</tbody></table></div> : <Empty icon={Store} title="No retailer workspaces yet" body="Create the first shop account to get started." />}
          <p className="field-hint">Suspending a shop blocks its users from signing in and revokes their access until you reactivate it. Shop data is retained.</p>
        </section>
      </div>
    </main>
  </div>;
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem("counterpoint_token"));
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(Boolean(localStorage.getItem("counterpoint_token")));
  useEffect(() => {
    if (!token) { setChecking(false); return; }
    request("/auth/me", token).then((currentUser) => { if (currentUser.currency) localStorage.setItem("counterpoint_currency", currentUser.currency); setUser(currentUser); }).catch(() => { localStorage.removeItem("counterpoint_token"); setToken(null); }).finally(() => setChecking(false));
  }, [token]);
  function authenticated(result) {
    localStorage.setItem("counterpoint_token", result.token);
    if (result.user.currency) localStorage.setItem("counterpoint_currency", result.user.currency);
    setToken(result.token); setUser(result.user);
  }
  function logout() { localStorage.removeItem("counterpoint_token"); setToken(null); setUser(null); }
  if (checking) return <div className="loading-screen"><span className="spinner" />Opening your store...</div>;
  if (token && user?.platform_owner) return <PlatformConsole key={token} token={token} user={user} onLogout={logout} />;
  return token && user ? <AppShell key={token} token={token} user={user} onLogout={logout} /> : <Auth onAuth={authenticated} />;
}
