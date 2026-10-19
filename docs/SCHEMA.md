# SCHEMA.md — MongoDB Schema Reference
## Inventory Stock Management System

---

## Collection: `products`

```json
{
  "_id":          ObjectId("..."),
  "sku":          "ELEC-001",
  "name":         "Wireless Bluetooth Headphones",
  "category":     "Electronics",
  "price":        2499.00,
  "quantity":     45,
  "reorder_level": 10,
  "supplier_id":  ObjectId("..."),
  "tags":         ["audio", "wireless", "bluetooth"],
  "created_at":   ISODate("2026-10-19T06:00:00Z"),
  "updated_at":   ISODate("2026-10-19T06:00:00Z")
}
```

**Indexes:**
| Index | Type | Fields |
|-------|------|--------|
| idx_products_sku_unique | Unique | `{ sku: 1 }` |
| idx_products_category | Regular | `{ category: 1 }` |
| idx_products_name_text | Text | `{ name: "text" }` |

---

## Collection: `suppliers`

```json
{
  "_id":       ObjectId("..."),
  "name":      "TechSupply India Pvt Ltd",
  "email":     "contact@techsupply.in",
  "phone":     "9876543210",
  "address":   "12, Tech Park, Bengaluru",
  "created_at": ISODate("2026-10-19T06:00:00Z")
}
```

**Indexes:**
| Index | Type | Fields |
|-------|------|--------|
| idx_suppliers_email_unique | Unique | `{ email: 1 }` |

---

## Collection: `transactions`

```json
{
  "_id":        ObjectId("..."),
  "product_id": ObjectId("..."),
  "type":       "IN",
  "quantity":   20,
  "note":       "PO-1042",
  "timestamp":  ISODate("2026-10-19T06:30:00Z")
}
```

**Indexes:**
| Index | Type | Fields |
|-------|------|--------|
| idx_transactions_product_time | Compound | `{ product_id: 1, timestamp: -1 }` |
