/**
 * app.js — InvenTrack Frontend Application
 * =========================================
 * Single-page application for the Inventory Stock Management System.
 * Communicates with the Flask REST API at /api/*
 */

const API = '';

// ─── State ───────────────────────────────────────────────────────────────────
let currentPage = 'dashboard';
let productsPage = 1;
let searchTimeout = null;
let categoriesCache = [];
let suppliersCache = [];

// ─── DOM References ──────────────────────────────────────────────────────────
const pageContent = document.getElementById('pageContent');
const pageTitle = document.getElementById('pageTitle');
const modalOverlay = document.getElementById('modalOverlay');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');
const modalClose = document.getElementById('modalClose');
const toastContainer = document.getElementById('toastContainer');
const searchInput = document.getElementById('searchInput');
const globalSearch = document.getElementById('globalSearch');
const menuToggle = document.getElementById('menuToggle');
const sidebar = document.getElementById('sidebar');

// ─── Navigation ──────────────────────────────────────────────────────────────
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', e => {
        e.preventDefault();
        const page = item.dataset.page;
        navigateTo(page);
    });
});

menuToggle.addEventListener('click', () => sidebar.classList.toggle('open'));

function navigateTo(page) {
    currentPage = page;
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelector(`[data-page="${page}"]`).classList.add('active');
    sidebar.classList.remove('open');

    globalSearch.style.display = page === 'products' ? 'flex' : 'none';

    const titles = {
        dashboard: ['Dashboard', 'Welcome to your inventory overview'],
        products: ['Products', 'Manage your product catalog'],
        suppliers: ['Suppliers', 'Manage your supplier network'],
        stock: ['Stock Operations', 'Record stock movements IN & OUT'],
        reports: ['Reports & Analytics', 'Insights into your inventory data'],
    };
    const [h, p] = titles[page] || ['', ''];
    pageTitle.innerHTML = `<h2>${h}</h2><p>${p}</p>`;

    const renderers = { dashboard: renderDashboard, products: renderProducts, suppliers: renderSuppliers, stock: renderStock, reports: renderReports };
    if (renderers[page]) renderers[page]();
}

// ─── Utility ─────────────────────────────────────────────────────────────────
async function apiFetch(url, opts = {}) {
    if (opts.body && typeof opts.body === 'object') {
        opts.body = JSON.stringify(opts.body);
        opts.headers = { 'Content-Type': 'application/json', ...opts.headers };
    }
    const res = await fetch(API + url, opts);
    return res.json();
}

function showToast(message, type = 'success') {
    const icons = {
        success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span class="toast-icon">${icons[type] || icons.success}</span><span>${message}</span>`;
    toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('toast-out');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function openModal(title, bodyHtml) {
    modalTitle.textContent = title;
    modalBody.innerHTML = bodyHtml;
    modalOverlay.classList.add('active');
}

function closeModal() {
    modalOverlay.classList.remove('active');
}

modalClose.addEventListener('click', closeModal);
modalOverlay.addEventListener('click', e => { if (e.target === modalOverlay) closeModal(); });

function formatDate(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatDateTime(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function formatCurrency(val) {
    return '₹' + Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function stockStatusBadge(quantity, reorderLevel) {
    if (quantity <= 0) return '<span class="badge badge-danger">Out of Stock</span>';
    if (quantity <= reorderLevel) return '<span class="badge badge-warning">Low Stock</span>';
    return '<span class="badge badge-success">In Stock</span>';
}

function spinner() {
    return '<div class="spinner"></div>';
}

// ─── Dashboard ───────────────────────────────────────────────────────────────
async function renderDashboard() {
    pageContent.innerHTML = `
        <div class="stats-grid" id="statsGrid">${Array(6).fill('<div class="stat-card"><div class="skeleton" style="height:100px;"></div></div>').join('')}</div>
        <div class="overview-grid" id="overviewGrid">${Array(2).fill('<div class="overview-card"><div class="skeleton" style="height:300px;"></div></div>').join('')}</div>
    `;

    const [dash, lowStock, topSold] = await Promise.all([
        apiFetch('/api/dashboard'),
        apiFetch('/api/reports/low-stock'),
        apiFetch('/api/reports/top-sold'),
    ]);

    const stats = [
        { label: 'Total Products', value: dash.total_products, icon: 'purple', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/></svg>' },
        { label: 'Total Suppliers', value: dash.total_suppliers, icon: 'blue', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>' },
        { label: 'Total Units', value: dash.total_units.toLocaleString(), icon: 'green', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="6" width="18" height="12" rx="2" ry="2"/><line x1="23" y1="13" x2="23" y2="11"/></svg>' },
        { label: 'Inventory Value', value: formatCurrency(dash.total_value), icon: 'orange', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>' },
        { label: 'Low Stock Items', value: dash.low_stock_count, icon: 'red', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>' },
        { label: 'Transactions', value: dash.total_transactions, icon: 'purple', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>' },
    ];

    document.getElementById('statsGrid').innerHTML = stats.map(s => `
        <div class="stat-card">
            <div class="stat-card-header">
                <span class="stat-card-label">${s.label}</span>
                <div class="stat-card-icon ${s.icon}">${s.svg}</div>
            </div>
            <div class="stat-card-value">${s.value}</div>
        </div>
    `).join('');

    // Low stock & top sold
    const lowStockHtml = lowStock.length === 0
        ? '<div class="empty-state" style="padding:30px;"><p>No low stock items 🎉</p></div>'
        : lowStock.slice(0, 8).map(p => `
            <div class="overview-list-item">
                <div class="overview-item-info">
                    <span class="overview-item-name">${p.name}</span>
                    <span class="overview-item-sub">${p.sku} · ${p.category}</span>
                </div>
                <span class="badge badge-warning">${p.quantity} left</span>
            </div>
        `).join('');

    const topSoldHtml = topSold.length === 0
        ? '<div class="empty-state" style="padding:30px;"><p>No sales data yet</p></div>'
        : topSold.map((p, i) => `
            <div class="overview-list-item">
                <div class="overview-item-info">
                    <span class="overview-item-name">${p.product_name}</span>
                    <span class="overview-item-sub">${p.sku} · ${p.category}</span>
                </div>
                <span class="badge badge-info">${p.total_sold} sold</span>
            </div>
        `).join('');

    document.getElementById('overviewGrid').innerHTML = `
        <div class="overview-card">
            <div class="overview-card-header">
                <h3>⚠️ Low Stock Alerts</h3>
                <button class="btn btn-sm btn-secondary" onclick="navigateTo('reports')">View All</button>
            </div>
            <div class="overview-card-body">${lowStockHtml}</div>
        </div>
        <div class="overview-card">
            <div class="overview-card-header">
                <h3>🏆 Top Selling Products</h3>
                <button class="btn btn-sm btn-secondary" onclick="navigateTo('reports')">View All</button>
            </div>
            <div class="overview-card-body">${topSoldHtml}</div>
        </div>
    `;
}

// ─── Products ────────────────────────────────────────────────────────────────
async function renderProducts(page = 1, search = '', category = '') {
    productsPage = page;
    pageContent.innerHTML = `
        <div class="section-header">
            <div class="filter-bar" id="filterBar">
                <select class="filter-select" id="categoryFilter"><option value="">All Categories</option></select>
            </div>
            <button class="btn btn-primary" onclick="openAddProductModal()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Add Product
            </button>
        </div>
        <div class="table-container">
            <div class="table-wrapper" id="productsTableWrapper">${spinner()}</div>
            <div id="productsPagination" class="pagination"></div>
        </div>
    `;

    // Load categories for filter
    if (categoriesCache.length === 0) {
        categoriesCache = await apiFetch('/api/categories');
    }
    const catFilter = document.getElementById('categoryFilter');
    categoriesCache.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c; opt.textContent = c;
        if (c === category) opt.selected = true;
        catFilter.appendChild(opt);
    });
    catFilter.addEventListener('change', () => renderProducts(1, '', catFilter.value));

    // Search
    searchInput.value = search;
    searchInput.oninput = () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => renderProducts(1, searchInput.value.trim(), ''), 400);
    };

    let url = `/api/products?page=${page}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (category) url += `&category=${encodeURIComponent(category)}`;

    const data = await apiFetch(url);
    const products = data.products || [];

    if (products.length === 0) {
        document.getElementById('productsTableWrapper').innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/></svg>
                <h3>No products found</h3>
                <p>Add your first product to get started</p>
            </div>`;
        return;
    }

    document.getElementById('productsTableWrapper').innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>SKU</th>
                    <th>Product Name</th>
                    <th>Category</th>
                    <th>Price</th>
                    <th>Quantity</th>
                    <th>Status</th>
                    <th>Tags</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${products.map(p => `
                    <tr>
                        <td><span class="badge badge-neutral">${p.sku}</span></td>
                        <td style="color:var(--text-primary);font-weight:600;">${p.name}</td>
                        <td>${p.category}</td>
                        <td>${formatCurrency(p.price)}</td>
                        <td style="font-weight:700;">${p.quantity}</td>
                        <td>${stockStatusBadge(p.quantity, p.reorder_level)}</td>
                        <td>${(p.tags || []).map(t => `<span class="tag-pill">${t}</span>`).join('') || '—'}</td>
                        <td>
                            <div class="action-btns">
                                <button class="action-btn edit-btn" title="Edit" onclick="openEditProductModal('${p.sku}')">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                                </button>
                                <button class="action-btn history-btn" title="History" onclick="showProductHistory('${p.sku}')">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                                </button>
                                <button class="action-btn delete-btn" title="Delete" onclick="confirmDeleteProduct('${p.sku}','${p.name.replace(/'/g, "\\'")}')">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                                </button>
                            </div>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    // Pagination
    if (data.total_pages > 1) {
        let pagHtml = `<button class="page-btn" ${page <= 1 ? 'disabled' : ''} onclick="renderProducts(${page - 1})">‹</button>`;
        for (let i = 1; i <= data.total_pages; i++) {
            pagHtml += `<button class="page-btn ${i === page ? 'active' : ''}" onclick="renderProducts(${i})">${i}</button>`;
        }
        pagHtml += `<button class="page-btn" ${page >= data.total_pages ? 'disabled' : ''} onclick="renderProducts(${page + 1})">›</button>`;
        document.getElementById('productsPagination').innerHTML = pagHtml;
    }
}

function openAddProductModal() {
    loadSuppliersCache().then(() => {
        const supplierOpts = suppliersCache.map(s => `<option value="${s._id}">${s.name}</option>`).join('');
        openModal('Add New Product', `
            <form id="addProductForm" class="form-grid" onsubmit="handleAddProduct(event)">
                <div class="form-group">
                    <label class="form-label">SKU *</label>
                    <input class="form-input" name="sku" placeholder="e.g. ELEC-001" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Product Name *</label>
                    <input class="form-input" name="name" placeholder="Product name" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Category *</label>
                    <input class="form-input" name="category" placeholder="e.g. Electronics" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Price *</label>
                    <input class="form-input" type="number" step="0.01" min="0.01" name="price" placeholder="0.00" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Quantity *</label>
                    <input class="form-input" type="number" min="0" name="quantity" placeholder="0" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Reorder Level</label>
                    <input class="form-input" type="number" min="0" name="reorder_level" value="10">
                </div>
                <div class="form-group">
                    <label class="form-label">Supplier</label>
                    <select class="form-select" name="supplier_id"><option value="">No Supplier</option>${supplierOpts}</select>
                </div>
                <div class="form-group">
                    <label class="form-label">Tags (comma-separated)</label>
                    <input class="form-input" name="tags" placeholder="e.g. sale, new, premium">
                </div>
                <div class="form-actions">
                    <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">Add Product</button>
                </div>
            </form>
        `);
    });
}

async function handleAddProduct(e) {
    e.preventDefault();
    const fd = new FormData(e.target);
    const tags = fd.get('tags') ? fd.get('tags').split(',').map(t => t.trim()).filter(Boolean) : [];
    const res = await apiFetch('/api/products', {
        method: 'POST',
        body: {
            sku: fd.get('sku'), name: fd.get('name'), category: fd.get('category'),
            price: fd.get('price'), quantity: fd.get('quantity'),
            reorder_level: fd.get('reorder_level') || 10,
            supplier_id: fd.get('supplier_id') || null, tags,
        },
    });
    if (res.success) {
        showToast('Product added successfully');
        closeModal();
        categoriesCache = [];
        renderProducts();
    } else {
        showToast(res.error || 'Failed to add product', 'error');
    }
}

async function openEditProductModal(sku) {
    const product = await apiFetch(`/api/products/${sku}`);
    if (!product || product.error) return showToast('Product not found', 'error');

    await loadSuppliersCache();
    const supplierOpts = suppliersCache.map(s => `<option value="${s._id}" ${s._id === product.supplier_id ? 'selected' : ''}>${s.name}</option>`).join('');

    openModal('Edit Product', `
        <form id="editProductForm" class="form-grid" onsubmit="handleEditProduct(event, '${sku}')">
            <div class="form-group">
                <label class="form-label">SKU</label>
                <input class="form-input" value="${product.sku}" disabled>
            </div>
            <div class="form-group">
                <label class="form-label">Product Name *</label>
                <input class="form-input" name="name" value="${product.name}" required>
            </div>
            <div class="form-group">
                <label class="form-label">Category *</label>
                <input class="form-input" name="category" value="${product.category}" required>
            </div>
            <div class="form-group">
                <label class="form-label">Price *</label>
                <input class="form-input" type="number" step="0.01" min="0.01" name="price" value="${product.price}" required>
            </div>
            <div class="form-group">
                <label class="form-label">Quantity</label>
                <input class="form-input" type="number" min="0" name="quantity" value="${product.quantity}" required>
            </div>
            <div class="form-group">
                <label class="form-label">Reorder Level</label>
                <input class="form-input" type="number" min="0" name="reorder_level" value="${product.reorder_level}">
            </div>
            <div class="form-group">
                <label class="form-label">Supplier</label>
                <select class="form-select" name="supplier_id"><option value="">No Supplier</option>${supplierOpts}</select>
            </div>
            <div class="form-group">
                <label class="form-label">Tags (comma-separated)</label>
                <input class="form-input" name="tags" value="${(product.tags || []).join(', ')}">
            </div>
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Save Changes</button>
            </div>
        </form>
    `);
}

async function handleEditProduct(e, sku) {
    e.preventDefault();
    const fd = new FormData(e.target);
    const tags = fd.get('tags') ? fd.get('tags').split(',').map(t => t.trim()).filter(Boolean) : [];
    const res = await apiFetch(`/api/products/${sku}`, {
        method: 'PUT',
        body: {
            name: fd.get('name'), category: fd.get('category'),
            price: fd.get('price'), quantity: fd.get('quantity'),
            reorder_level: fd.get('reorder_level'),
            supplier_id: fd.get('supplier_id') || null, tags,
        },
    });
    if (res.success) {
        showToast('Product updated successfully');
        closeModal();
        categoriesCache = [];
        renderProducts(productsPage);
    } else {
        showToast(res.error || 'Failed to update', 'error');
    }
}

function confirmDeleteProduct(sku, name) {
    openModal('Delete Product', `
        <p class="confirm-message">Are you sure you want to delete <strong>${name}</strong> (${sku})?<br>This action cannot be undone.</p>
        <div class="confirm-actions">
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn btn-danger" onclick="handleDeleteProduct('${sku}')">Delete</button>
        </div>
    `);
}

async function handleDeleteProduct(sku) {
    const res = await apiFetch(`/api/products/${sku}`, { method: 'DELETE' });
    if (res.success) {
        showToast('Product deleted');
        closeModal();
        categoriesCache = [];
        renderProducts(productsPage);
    } else {
        showToast(res.error || 'Failed to delete', 'error');
    }
}

async function showProductHistory(sku) {
    openModal(`Transaction History — ${sku}`, spinner());
    const history = await apiFetch(`/api/stock/history/${sku}`);
    if (history.length === 0) {
        modalBody.innerHTML = '<div class="empty-state"><p>No transactions recorded for this product</p></div>';
        return;
    }
    modalBody.innerHTML = `<div class="history-list">${history.map(h => `
        <div class="history-item">
            <div class="history-left">
                <div class="history-type-icon ${h.type.toLowerCase()}">${h.type === 'IN' ? '↓' : '↑'}</div>
                <div class="history-info">
                    <span class="history-qty">${h.type === 'IN' ? '+' : '-'}${h.quantity} units</span>
                    <span class="history-note">${h.note || 'No note'}</span>
                </div>
            </div>
            <span class="history-time">${formatDateTime(h.timestamp)}</span>
        </div>
    `).join('')}</div>`;
}

// ─── Suppliers ───────────────────────────────────────────────────────────────
async function loadSuppliersCache() {
    suppliersCache = await apiFetch('/api/suppliers');
}

async function renderSuppliers() {
    pageContent.innerHTML = `
        <div class="section-header">
            <span class="section-title">All Suppliers</span>
            <button class="btn btn-primary" onclick="openAddSupplierModal()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Add Supplier
            </button>
        </div>
        <div class="table-container">
            <div class="table-wrapper" id="suppliersTableWrapper">${spinner()}</div>
        </div>
    `;

    const suppliers = await apiFetch('/api/suppliers');
    suppliersCache = suppliers;

    if (suppliers.length === 0) {
        document.getElementById('suppliersTableWrapper').innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
                <h3>No suppliers yet</h3>
                <p>Add your first supplier to get started</p>
            </div>`;
        return;
    }

    document.getElementById('suppliersTableWrapper').innerHTML = `
        <table>
            <thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>Address</th><th>Joined</th><th>Actions</th></tr></thead>
            <tbody>
                ${suppliers.map(s => `
                    <tr>
                        <td style="color:var(--text-primary);font-weight:600;">${s.name}</td>
                        <td>${s.email}</td>
                        <td>${s.phone || '—'}</td>
                        <td>${s.address || '—'}</td>
                        <td>${formatDate(s.created_at)}</td>
                        <td>
                            <div class="action-btns">
                                <button class="action-btn edit-btn" title="Edit" onclick="openEditSupplierModal('${s._id}')">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                                </button>
                                <button class="action-btn delete-btn" title="Delete" onclick="confirmDeleteSupplier('${s._id}','${s.name.replace(/'/g, "\\'")}')">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                                </button>
                            </div>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function openAddSupplierModal() {
    openModal('Add New Supplier', `
        <form id="addSupplierForm" class="form-grid" onsubmit="handleAddSupplier(event)">
            <div class="form-group">
                <label class="form-label">Company Name *</label>
                <input class="form-input" name="name" placeholder="Supplier name" required>
            </div>
            <div class="form-group">
                <label class="form-label">Email *</label>
                <input class="form-input" type="email" name="email" placeholder="email@example.com" required>
            </div>
            <div class="form-group">
                <label class="form-label">Phone</label>
                <input class="form-input" name="phone" placeholder="Phone number">
            </div>
            <div class="form-group">
                <label class="form-label">Address</label>
                <input class="form-input" name="address" placeholder="Physical address">
            </div>
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Add Supplier</button>
            </div>
        </form>
    `);
}

async function handleAddSupplier(e) {
    e.preventDefault();
    const fd = new FormData(e.target);
    const res = await apiFetch('/api/suppliers', {
        method: 'POST',
        body: { name: fd.get('name'), email: fd.get('email'), phone: fd.get('phone'), address: fd.get('address') },
    });
    if (res.success) {
        showToast('Supplier added successfully');
        closeModal();
        renderSuppliers();
    } else {
        showToast(res.error || 'Failed to add supplier', 'error');
    }
}

async function openEditSupplierModal(id) {
    const supplier = await apiFetch(`/api/suppliers/${id}`);
    if (!supplier || supplier.error) return showToast('Supplier not found', 'error');

    openModal('Edit Supplier', `
        <form class="form-grid" onsubmit="handleEditSupplier(event, '${id}')">
            <div class="form-group">
                <label class="form-label">Company Name *</label>
                <input class="form-input" name="name" value="${supplier.name}" required>
            </div>
            <div class="form-group">
                <label class="form-label">Email *</label>
                <input class="form-input" type="email" name="email" value="${supplier.email}" required>
            </div>
            <div class="form-group">
                <label class="form-label">Phone</label>
                <input class="form-input" name="phone" value="${supplier.phone || ''}">
            </div>
            <div class="form-group">
                <label class="form-label">Address</label>
                <input class="form-input" name="address" value="${supplier.address || ''}">
            </div>
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn btn-primary">Save Changes</button>
            </div>
        </form>
    `);
}

async function handleEditSupplier(e, id) {
    e.preventDefault();
    const fd = new FormData(e.target);
    const res = await apiFetch(`/api/suppliers/${id}`, {
        method: 'PUT',
        body: { name: fd.get('name'), email: fd.get('email'), phone: fd.get('phone'), address: fd.get('address') },
    });
    if (res.success) {
        showToast('Supplier updated');
        closeModal();
        renderSuppliers();
    } else {
        showToast(res.error || 'Failed to update', 'error');
    }
}

function confirmDeleteSupplier(id, name) {
    openModal('Delete Supplier', `
        <p class="confirm-message">Are you sure you want to delete <strong>${name}</strong>?<br>This will fail if products are linked to this supplier.</p>
        <div class="confirm-actions">
            <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            <button class="btn btn-danger" onclick="handleDeleteSupplier('${id}')">Delete</button>
        </div>
    `);
}

async function handleDeleteSupplier(id) {
    const res = await apiFetch(`/api/suppliers/${id}`, { method: 'DELETE' });
    if (res.success) {
        showToast('Supplier deleted');
        closeModal();
        renderSuppliers();
    } else {
        showToast(res.error || 'Failed to delete', 'error');
    }
}

// ─── Stock Operations ────────────────────────────────────────────────────────
function renderStock() {
    pageContent.innerHTML = `
        <div class="stock-ops-grid">
            <div class="stock-op-card stock-in-card">
                <div class="stock-op-title">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>
                    Stock IN (Purchase / Receive)
                </div>
                <form class="form-grid" onsubmit="handleStockOp(event, 'in')" style="grid-template-columns:1fr;">
                    <div class="form-group">
                        <label class="form-label">Product SKU *</label>
                        <input class="form-input" name="sku" placeholder="e.g. ELEC-001" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Quantity *</label>
                        <input class="form-input" type="number" min="1" name="quantity" placeholder="Number of units" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Note</label>
                        <input class="form-input" name="note" placeholder="e.g. PO-1042 from supplier">
                    </div>
                    <button type="submit" class="btn btn-success" style="width:100%;justify-content:center;">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                        Record Stock IN
                    </button>
                </form>
            </div>
            <div class="stock-op-card stock-out-card">
                <div class="stock-op-title">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg>
                    Stock OUT (Sale / Dispatch)
                </div>
                <form class="form-grid" onsubmit="handleStockOp(event, 'out')" style="grid-template-columns:1fr;">
                    <div class="form-group">
                        <label class="form-label">Product SKU *</label>
                        <input class="form-input" name="sku" placeholder="e.g. ELEC-001" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Quantity *</label>
                        <input class="form-input" type="number" min="1" name="quantity" placeholder="Number of units" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Note</label>
                        <input class="form-input" name="note" placeholder="e.g. Invoice #5021, Customer XYZ">
                    </div>
                    <button type="submit" class="btn btn-danger" style="width:100%;justify-content:center;">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/></svg>
                        Record Stock OUT
                    </button>
                </form>
            </div>
        </div>
        <div class="section-header">
            <span class="section-title">Recent Transactions</span>
            <div class="filter-bar">
                <input class="form-input" id="historySkuInput" placeholder="Enter SKU to view history" style="max-width:240px;">
                <button class="btn btn-secondary" onclick="loadHistory()">Load History</button>
            </div>
        </div>
        <div id="historyContainer"></div>
    `;
}

async function handleStockOp(e, type) {
    e.preventDefault();
    const fd = new FormData(e.target);
    const res = await apiFetch(`/api/stock/${type}`, {
        method: 'POST',
        body: { sku: fd.get('sku'), quantity: fd.get('quantity'), note: fd.get('note') || '' },
    });
    if (res.success) {
        showToast(`Stock ${type.toUpperCase()} recorded — ${res.product_name}: new qty = ${res.new_quantity}`);
        e.target.reset();
    } else {
        showToast(res.error || `Stock ${type.toUpperCase()} failed`, 'error');
    }
}

async function loadHistory() {
    const sku = document.getElementById('historySkuInput').value.trim();
    if (!sku) return showToast('Please enter a SKU', 'warning');

    const container = document.getElementById('historyContainer');
    container.innerHTML = spinner();

    const history = await apiFetch(`/api/stock/history/${sku}`);
    if (history.length === 0) {
        container.innerHTML = `
            <div class="table-container">
                <div class="empty-state"><p>No transactions found for SKU: ${sku}</p></div>
            </div>`;
        return;
    }

    container.innerHTML = `
        <div class="table-container">
            <div class="table-wrapper">
                <table>
                    <thead><tr><th>Type</th><th>Quantity</th><th>Note</th><th>Timestamp</th></tr></thead>
                    <tbody>
                        ${history.map(h => `
                            <tr>
                                <td><span class="badge ${h.type === 'IN' ? 'stock-badge-in' : 'stock-badge-out'}">${h.type === 'IN' ? '↓ IN' : '↑ OUT'}</span></td>
                                <td style="font-weight:700;">${h.type === 'IN' ? '+' : '-'}${h.quantity}</td>
                                <td>${h.note || '—'}</td>
                                <td>${formatDateTime(h.timestamp)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// ─── Reports ─────────────────────────────────────────────────────────────────
async function renderReports() {
    pageContent.innerHTML = `
        <div class="section-header">
            <span class="section-title">Analytics & Reports</span>
            <button class="btn btn-secondary" onclick="handleExportCsv()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                Export CSV
            </button>
        </div>
        <div class="report-grid" id="reportsGrid">${Array(5).fill('<div class="report-card"><div class="skeleton" style="height:200px;"></div></div>').join('')}</div>
    `;

    const [lowStock, catVal, supplierSum, monthly, topSold] = await Promise.all([
        apiFetch('/api/reports/low-stock'),
        apiFetch('/api/reports/category-value'),
        apiFetch('/api/reports/supplier-summary'),
        apiFetch('/api/reports/monthly-movement'),
        apiFetch('/api/reports/top-sold'),
    ]);

    const months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    document.getElementById('reportsGrid').innerHTML = `
        <!-- Low Stock -->
        <div class="report-card">
            <div class="report-card-header">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                <h4>Low Stock Alerts (${lowStock.length})</h4>
            </div>
            <div class="report-card-body">
                ${lowStock.length === 0 ? '<p style="color:var(--text-muted);">All products are well-stocked 🎉</p>' :
                  `<table><thead><tr><th>SKU</th><th>Name</th><th>Qty</th><th>Reorder</th></tr></thead><tbody>
                  ${lowStock.map(p => `<tr><td><span class="badge badge-neutral">${p.sku}</span></td><td>${p.name}</td><td style="font-weight:700;color:var(--warning);">${p.quantity}</td><td>${p.reorder_level}</td></tr>`).join('')}
                  </tbody></table>`}
            </div>
        </div>

        <!-- Category Value -->
        <div class="report-card">
            <div class="report-card-header">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
                <h4>Category Stock Value</h4>
            </div>
            <div class="report-card-body">
                ${catVal.length === 0 ? '<p style="color:var(--text-muted);">No data</p>' :
                  `<table><thead><tr><th>Category</th><th>Products</th><th>Units</th><th>Value</th></tr></thead><tbody>
                  ${catVal.map(c => `<tr><td style="font-weight:600;color:var(--text-primary);">${c.category}</td><td>${c.total_products}</td><td>${c.total_quantity}</td><td style="font-weight:600;">${formatCurrency(c.total_value)}</td></tr>`).join('')}
                  </tbody></table>`}
            </div>
        </div>

        <!-- Supplier Summary -->
        <div class="report-card">
            <div class="report-card-header">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
                <h4>Supplier Summary</h4>
            </div>
            <div class="report-card-body">
                ${supplierSum.length === 0 ? '<p style="color:var(--text-muted);">No data</p>' :
                  `<table><thead><tr><th>Supplier</th><th>Products</th><th>Value</th></tr></thead><tbody>
                  ${supplierSum.map(s => `<tr><td><div class="supplier-detail"><span class="name">${s.supplier_name}</span><span class="email">${s.supplier_email}</span></div></td><td>${s.product_count}</td><td style="font-weight:600;">${formatCurrency(s.total_value)}</td></tr>`).join('')}
                  </tbody></table>`}
            </div>
        </div>

        <!-- Monthly Movement -->
        <div class="report-card">
            <div class="report-card-header">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                <h4>Monthly Movement</h4>
            </div>
            <div class="report-card-body">
                ${monthly.length === 0 ? '<p style="color:var(--text-muted);">No transactions yet</p>' :
                  `<table><thead><tr><th>Period</th><th>Type</th><th>Qty</th><th>Txns</th></tr></thead><tbody>
                  ${monthly.map(m => `<tr><td>${months[m.month]} ${m.year}</td><td><span class="badge ${m.type === 'IN' ? 'stock-badge-in' : 'stock-badge-out'}">${m.type}</span></td><td style="font-weight:700;">${m.total_quantity}</td><td>${m.transaction_count}</td></tr>`).join('')}
                  </tbody></table>`}
            </div>
        </div>

        <!-- Top Sold -->
        <div class="report-card">
            <div class="report-card-header">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                <h4>Top 5 Sold Products</h4>
            </div>
            <div class="report-card-body">
                ${topSold.length === 0 ? '<p style="color:var(--text-muted);">No sales data yet</p>' :
                  `<table><thead><tr><th>Product</th><th>SKU</th><th>Sold</th><th>Txns</th></tr></thead><tbody>
                  ${topSold.map(p => `<tr><td style="font-weight:600;color:var(--text-primary);">${p.product_name}</td><td><span class="badge badge-neutral">${p.sku}</span></td><td style="font-weight:700;color:var(--accent-primary-light);">${p.total_sold}</td><td>${p.transaction_count}</td></tr>`).join('')}
                  </tbody></table>`}
            </div>
        </div>
    `;
}

async function handleExportCsv() {
    const res = await apiFetch('/api/export/csv', { method: 'POST' });
    if (res.success) {
        showToast(`Exported ${res.count} products to ${res.filepath}`);
    } else {
        showToast(res.error || 'Export failed', 'error');
    }
}

// ─── Boot ────────────────────────────────────────────────────────────────────
navigateTo('dashboard');
