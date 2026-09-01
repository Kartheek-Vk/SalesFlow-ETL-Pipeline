-- SalesFlow's serving queries. The Python functions in
-- salesflow/analytics/queries.py execute these same statements against SQLite.

-- 1. Total revenue, orders, average order value, discount, cancellations
SELECT
    SUM(net_revenue) AS total_revenue,
    COUNT(DISTINCT order_id) AS total_orders,
    AVG(net_revenue) AS average_order_value,
    SUM(discount_amount) AS total_discount,
    SUM(CASE WHEN order_status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders
FROM sales_fact;

-- 2. Top 10 products
SELECT product_id, product_name, category, orders, units_sold, net_revenue
FROM product_sales_summary
ORDER BY net_revenue DESC
LIMIT 10;

-- 3. Category and state revenue
SELECT category, SUM(net_revenue) AS revenue
FROM sales_fact
GROUP BY category
ORDER BY revenue DESC;

SELECT state, SUM(net_revenue) AS revenue
FROM sales_fact
GROUP BY state
ORDER BY revenue DESC;

-- 4. Revenue by month and day
SELECT order_month, SUM(net_revenue) AS revenue
FROM sales_fact
GROUP BY order_month
ORDER BY order_month;

SELECT order_date, COUNT(DISTINCT order_id) AS orders, SUM(net_revenue) AS revenue
FROM sales_fact
GROUP BY order_date
ORDER BY order_date;

-- 5. Repeat customers and purchase frequency
SELECT customer_id, customer_name, COUNT(DISTINCT order_id) AS orders
FROM sales_fact
GROUP BY customer_id, customer_name
HAVING orders > 1
ORDER BY orders DESC;

SELECT orders, COUNT(*) AS customers
FROM (
    SELECT customer_id, COUNT(DISTINCT order_id) AS orders
    FROM sales_fact
    GROUP BY customer_id
)
GROUP BY orders
ORDER BY orders;

-- 6. Discount impact
SELECT
    SUM(discount_amount) AS discount_amount,
    SUM(gross_revenue) AS gross_revenue,
    SUM(net_revenue) AS net_revenue
FROM sales_fact;

-- 7. Cancelled order monitoring
SELECT order_id, order_date, customer_name, product_name, gross_revenue
FROM sales_fact
WHERE order_status = 'cancelled'
ORDER BY order_date DESC;