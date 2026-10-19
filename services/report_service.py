"""
services/report_service.py
---------------------------
All 5 aggregation-pipeline reports for the inventory system.

MongoDB Aggregation Pipeline:
    A pipeline is an array of stages. Each stage transforms the documents
    and passes its output to the next stage. Think of it like a Unix pipe:
        collection → [$match] → [$group] → [$sort] → [$limit] → result

Pipeline stages used in this file:
    $match  – filter documents (like WHERE in SQL)
    $group  – group and aggregate (like GROUP BY + SUM/COUNT in SQL)
    $sort   – order results
    $limit  – take top N results
    $lookup – join with another collection (like LEFT JOIN in SQL)
    $project – reshape output documents (like SELECT in SQL)
    $unwind – flatten an array field into separate documents

This file is the most academically important one — aggregation pipelines
are a key exam/viva topic for MongoDB courses.
"""

from db.connection import get_collection


def low_stock_report(db_name: str = None) -> list[dict]:
    """
    Report 1: Products where current quantity <= reorder_level.

    This is a simple find() with a field comparison filter.
    MongoDB supports comparing two fields within the same document
    using $expr with $lte.

    Args:
        db_name: Optional DB override.

    Returns:
        list[dict]: Products at or below reorder level, sorted by quantity asc.
    """
    col = get_collection("products", db_name) if db_name else get_collection("products")

    # $expr allows using aggregation expressions inside a query filter.
    # Here we compare two fields of the SAME document: quantity vs reorder_level.
    results = list(
        col.find(
            {"$expr": {"$lte": ["$quantity", "$reorder_level"]}}
        ).sort("quantity", 1)  # lowest stock first
    )
    return results


def category_stock_value_report(db_name: str = None) -> list[dict]:
    """
    Report 2: Total stock value grouped by category.

    Pipeline:
        $group by category
            → count total products ($sum: 1)
            → sum total quantity ($sum: "$quantity")
            → sum total value = price × quantity ($sum of $multiply)
        $sort by total_value descending

    $multiply: ["$price", "$quantity"] computes price * quantity per document.
    $sum: {...} then adds up all those values within each group.

    Args:
        db_name: Optional DB override.

    Returns:
        list[dict]: One document per category with aggregated totals.
    """
    col = get_collection("products", db_name) if db_name else get_collection("products")

    pipeline = [
        {
            "$group": {
                "_id": "$category",                      # GROUP BY category
                "total_products": {"$sum": 1},           # COUNT(*)
                "total_quantity": {"$sum": "$quantity"},  # SUM(quantity)
                "total_value": {
                    # SUM(price * quantity) — $multiply returns an array result
                    "$sum": {"$multiply": ["$price", "$quantity"]}
                },
            }
        },
        {
            "$sort": {"total_value": -1}   # highest value category first
        },
        {
            # Rename _id to category for cleaner display
            "$project": {
                "category": "$_id",
                "total_products": 1,
                "total_quantity": 1,
                "total_value": {"$round": ["$total_value", 2]},
                "_id": 0,
            }
        },
    ]

    return list(col.aggregate(pipeline))


def supplier_summary_report(db_name: str = None) -> list[dict]:
    """
    Report 3: Supplier-wise product count and total stock value.

    Pipeline on 'products' collection:
        $group by supplier_id
            → count products, sum quantity, compute value
        $lookup → join with 'suppliers' to get supplier name
        $unwind the joined supplier array (it's always 0 or 1 element)
        $project → clean output
        $sort by total_value desc

    $lookup is MongoDB's equivalent of SQL LEFT JOIN:
        from:         the collection to join
        localField:   field in the current (products) collection
        foreignField: field in the joined (suppliers) collection
        as:           name of the new array field added to each document

    Args:
        db_name: Optional DB override.

    Returns:
        list[dict]: One row per supplier with product count and stock value.
    """
    col = get_collection("products", db_name) if db_name else get_collection("products")

    pipeline = [
        # Stage 1: Group products by supplier_id
        {
            "$group": {
                "_id": "$supplier_id",
                "product_count": {"$sum": 1},
                "total_quantity": {"$sum": "$quantity"},
                "total_value": {
                    "$sum": {"$multiply": ["$price", "$quantity"]}
                },
            }
        },
        # Stage 2: $lookup joins the suppliers collection on _id = supplier_id
        {
            "$lookup": {
                "from": "suppliers",          # collection to join
                "localField": "_id",          # field in current docs (supplier_id)
                "foreignField": "_id",        # field in suppliers docs
                "as": "supplier_info",        # result stored in this array field
            }
        },
        # Stage 3: $unwind flattens the supplier_info array.
        # preserveNullAndEmptyArrays=True keeps products with no supplier.
        {
            "$unwind": {
                "path": "$supplier_info",
                "preserveNullAndEmptyArrays": True,
            }
        },
        # Stage 4: Reshape the output document
        {
            "$project": {
                "_id": 0,
                "supplier_name": {
                    "$ifNull": ["$supplier_info.name", "No Supplier"]
                },
                "supplier_email": {
                    "$ifNull": ["$supplier_info.email", "-"]
                },
                "product_count": 1,
                "total_quantity": 1,
                "total_value": {"$round": ["$total_value", 2]},
            }
        },
        {"$sort": {"total_value": -1}},
    ]

    return list(col.aggregate(pipeline))


def monthly_movement_report(db_name: str = None) -> list[dict]:
    """
    Report 4: Monthly stock movement summary from the transactions collection.

    Pipeline on 'transactions':
        $group by (year, month, type)
            → sum total quantity moved
            → count number of transactions
        $sort by year desc, month desc, type asc

    $dateToString / $year / $month extract parts of a datetime field.

    Args:
        db_name: Optional DB override.

    Returns:
        list[dict]: Monthly breakdown of IN vs OUT movements.
    """
    col = (
        get_collection("transactions", db_name) if db_name
        else get_collection("transactions")
    )

    pipeline = [
        # Stage 1: Group by year + month + movement type
        {
            "$group": {
                "_id": {
                    # $year and $month extract components from the datetime field
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                    "type": "$type",
                },
                "total_quantity": {"$sum": "$quantity"},
                "transaction_count": {"$sum": 1},
            }
        },
        # Stage 2: Reshape for cleaner display
        {
            "$project": {
                "_id": 0,
                "year": "$_id.year",
                "month": "$_id.month",
                "type": "$_id.type",
                "total_quantity": 1,
                "transaction_count": 1,
            }
        },
        # Stage 3: Sort newest first
        {
            "$sort": {"year": -1, "month": -1, "type": 1}
        },
    ]

    return list(col.aggregate(pipeline))


def top_sold_products_report(db_name: str = None) -> list[dict]:
    """
    Report 5: Top 5 most sold products by total Stock OUT quantity.

    Pipeline on 'transactions':
        $match type == "OUT"
        $group by product_id → sum quantity
        $sort by total_sold desc
        $limit 5
        $lookup → join products to get product name and SKU
        $unwind the product info array

    This is a multi-stage pipeline combining $match, $group, $sort,
    $limit, and $lookup — a great demonstration for exam marks.

    Args:
        db_name: Optional DB override.

    Returns:
        list[dict]: Top 5 products with their total sold quantities.
    """
    col = (
        get_collection("transactions", db_name) if db_name
        else get_collection("transactions")
    )

    pipeline = [
        # Stage 1: Only look at Stock OUT transactions
        {
            "$match": {"type": "OUT"}
        },
        # Stage 2: Group by product_id and sum up quantities sold
        {
            "$group": {
                "_id": "$product_id",
                "total_sold": {"$sum": "$quantity"},
                "transaction_count": {"$sum": 1},
            }
        },
        # Stage 3: Sort by most sold first
        {
            "$sort": {"total_sold": -1}
        },
        # Stage 4: Keep only top 5
        {
            "$limit": 5
        },
        # Stage 5: Join with products collection to get name and SKU
        {
            "$lookup": {
                "from": "products",
                "localField": "_id",        # product_id in transactions
                "foreignField": "_id",      # _id in products
                "as": "product_info",
            }
        },
        # Stage 6: Flatten the product_info array (each doc joins one product)
        {
            "$unwind": {
                "path": "$product_info",
                "preserveNullAndEmptyArrays": True,
            }
        },
        # Stage 7: Clean up the output
        {
            "$project": {
                "_id": 0,
                "sku": {"$ifNull": ["$product_info.sku", "DELETED"]},
                "product_name": {"$ifNull": ["$product_info.name", "Deleted Product"]},
                "category": {"$ifNull": ["$product_info.category", "-"]},
                "total_sold": 1,
                "transaction_count": 1,
            }
        },
    ]

    return list(col.aggregate(pipeline))
