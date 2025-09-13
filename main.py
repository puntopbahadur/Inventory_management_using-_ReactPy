from reactpy import component, html, run, hooks
import mysql.connector

# MySQL database configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "2846",
    "database": "mydatabase"
}

def connect_to_db():
    return mysql.connector.connect(**db_config)

def fetch_inventory():
    conn = connect_to_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM inventory")
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return items

def insert_item_into_db(name, quantity, price):
    conn = connect_to_db()
    cursor = conn.cursor()
    sql = "INSERT INTO inventory (name, quantity, price) VALUES (%s, %s, %s)"
    cursor.execute(sql, (name, quantity, price))
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return new_id

def update_item_quantity_in_db(item_id, new_quantity):
    conn = connect_to_db()
    cursor = conn.cursor()
    sql = "UPDATE inventory SET quantity = %s WHERE id = %s"
    cursor.execute(sql, (new_quantity, item_id))
    conn.commit()
    cursor.close()
    conn.close()

def delete_item_from_db(item_id):
    conn = connect_to_db()
    cursor = conn.cursor()
    sql = "DELETE FROM inventory WHERE id = %s"
    cursor.execute(sql, (item_id,))
    conn.commit()
    cursor.close()
    conn.close()

@component
def InventoryApp():
    # ✅ Start empty, load from DB once
    inventory, set_inventory = hooks.use_state([])
    sales, set_sales = hooks.use_state([])
    new_name, set_new_name = hooks.use_state("")
    new_qty, set_new_qty = hooks.use_state("")
    new_price, set_new_price = hooks.use_state("")
    sale_qty_inputs, set_sale_qty_inputs = hooks.use_state({})

    # Load items on mount
    def load_inventory():
        set_inventory(fetch_inventory())

    hooks.use_effect(load_inventory, [])

    def handle_sales_qty_change(item_id):
        def handler(event):
            value = event["target"]["value"]
            set_sale_qty_inputs({**sale_qty_inputs, item_id: value})
        return handler

    def add_item(event):
        if not new_name or not new_qty or not new_price:
            return
        try:
            qty = int(new_qty)
            price = float(new_price)
            if qty <= 0 or price <= 0:
                raise ValueError
        except ValueError:
            return

        insert_item_into_db(new_name, qty, price)
        load_inventory()  # ✅ reload from DB
        set_new_name("")
        set_new_qty("")
        set_new_price("")

    def sell_item(item_id):
        def handler(event):
            qty_str = sale_qty_inputs.get(item_id, "1")
            try:
                qty = int(qty_str)
                if qty <= 0:
                    raise ValueError
            except ValueError:
                qty = 1

            sold_item = next((item for item in inventory if item["id"] == item_id), None)
            if sold_item and sold_item["quantity"] > 0:
                sell_qty = min(qty, sold_item["quantity"])
                new_quantity = sold_item["quantity"] - sell_qty

                if new_quantity > 0:
                    update_item_quantity_in_db(item_id, new_quantity)
                else:
                    delete_item_from_db(item_id)

                load_inventory()  # ✅ always reload DB state

                set_sales(sales + [{
                    "item": sold_item["name"],
                    "price": sold_item["price"] * sell_qty,
                    "qty": sell_qty
                }])
                set_sale_qty_inputs({**sale_qty_inputs, item_id: ""})
        return handler

    return html.div(
        {"style": {
            "fontFamily": "Segoe UI, Arial, sans-serif",
            "background": "#f4f6fb",
            "minHeight": "100vh",
            "padding": "40px 0"
        }},
        html.div(
            {"style": {
                "maxWidth": "700px",
                "margin": "0 auto",
                "background": "#fff",
                "borderRadius": "12px",
                "boxShadow": "0 4px 24px rgba(0,0,0,0.08)",
                "padding": "28px 32px"
            }},
            html.h1({"style": {
                "color": "#2d3a4a",
                "fontWeight": 700,
                "fontSize": "1.8rem",
                "marginBottom": "20px",
                "textAlign": "center"
            }}, "Inventory Management"),

            # Inventory
            html.h2({"style": {"color": "#4a5a6a"}}, "Inventory"),
            html.ul(
                {"style": {"listStyle": "none", "padding": 0, "marginBottom": "24px"}},
                [
                    html.li(
                        {"key": item["id"], "style": {
                            "display": "flex", "alignItems": "center",
                            "justifyContent": "space-between",
                            "padding": "8px 0",
                            "borderBottom": "1px solid #eee"
                        }},
                        html.span(f'{item["name"]} - {item["quantity"]} left (${item["price"]:.2f})'),
                        html.div(
                            {"style": {"display": "flex", "gap": "10px", "alignItems": "center"}},
                            html.input({
                                "type": "number",
                                "value": sale_qty_inputs.get(item["id"], ""),
                                "placeholder": "Qty",
                                "on_change": handle_sales_qty_change(item["id"]),
                                "style": {"padding": "6px 10px", "borderRadius": "6px", "border": "1px solid #cfd8dc", "width": "70px"}
                            }),
                            html.button(
                                {
                                    "on_click": sell_item(item["id"]),
                                    "style": {"background": "#e53935", "color": "#fff", "border": "none",
                                              "borderRadius": "6px", "padding": "6px 12px",
                                              "cursor": "pointer", "fontWeight": 600,
                                              "transition": "background 0.2s"},
                                    "on_mouse_over": lambda e: e["target"].update(
                                        {"style": {**e["target"].get("style", {}), "background": "#c62828"}}),
                                    "on_mouse_out": lambda e: e["target"].update(
                                        {"style": {**e["target"].get("style", {}), "background": "#e53935"}})
                                },
                                "Sell"
                            )
                        )
                    )
                    for item in inventory
                ]
            ),

            # Add item
            html.h2({"style": {"color": "#4a5a6a"}}, "Add New Item"),
            html.div(
                {"style": {"display": "flex", "gap": "10px", "flexWrap": "wrap", "marginBottom": "20px"}},
                html.input({"placeholder": "Name", "value": new_name,
                            "on_change": lambda e: set_new_name(e["target"]["value"]),
                            "style": {"padding": "8px 10px", "borderRadius": "6px",
                                      "border": "1px solid #cfd8dc", "flex": "1"}}),
                html.input({"placeholder": "Quantity", "value": new_qty,
                            "on_change": lambda e: set_new_qty(e["target"]["value"]),
                            "style": {"padding": "8px 10px", "borderRadius": "6px",
                                      "border": "1px solid #cfd8dc", "width": "90px"}}),
                html.input({"placeholder": "Price", "value": new_price,
                            "on_change": lambda e: set_new_price(e["target"]["value"]),
                            "style": {"padding": "8px 10px", "borderRadius": "6px",
                                      "border": "1px solid #cfd8dc", "width": "100px"}}),
                html.button(
                    {
                        "on_click": add_item,
                        "style": {"background": "#1976d2", "color": "#fff", "border": "none",
                                  "borderRadius": "6px", "padding": "8px 16px",
                                  "fontWeight": 600, "cursor": "pointer", "transition": "background 0.2s"},
                        "on_mouse_over": lambda e: e["target"].update(
                            {"style": {**e["target"].get("style", {}), "background": "#1565c0"}}),
                        "on_mouse_out": lambda e: e["target"].update(
                            {"style": {**e["target"].get("style", {}), "background": "#1976d2"}})
                    }, "Add"
                )
            ),

            # Sales log
            html.h2({"style": {"color": "#4a5a6a"}}, "Sales Log"),
            html.ul(
                {"style": {"listStyle": "none", "padding": 0, "margin": 0}},
                [
                    html.li(
                        {"key": idx, "style": {"padding": "6px 0", "borderBottom": "1px solid #eee"}},
                        f'{sale["qty"]} x {sale["item"]} = ${sale["price"]:.2f}'
                    )
                    for idx, sale in enumerate(sales)
                ]
            )
        )
    )

run(InventoryApp)
