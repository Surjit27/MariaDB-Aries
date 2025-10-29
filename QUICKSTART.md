# 🚀 Quick Start Guide - AI Pipeline

## Step 1: Fix Corrupted JSON Files (First Time Only)

```bash
cd C:\Users\Meges\Downloads\MariaDB-Aries
python fix_json_files.py
```

This will:
- Backup any existing corrupted JSON files
- Create fresh query_history.json
- Create fresh favorites.json
- Create fresh schemas.json

## Step 2: Run the Application

```bash
python main.py
```

## Step 3: Use AI Query Assistant

### Method 1: Right-Click in Editor
1. Right-click anywhere in the SQL editor
2. Select "🤖 AI Query Assistant"

### Method 2: Keyboard Shortcut (Can be added)
- Press `Ctrl+Shift+A` (if you add the binding)

## How to Use AI Assistant

### For New Query:
1. Select tables in left panel (or select all)
2. Choose mode: 🆕 **Generate New Query**
3. Enter prompt: "Show all customers who bought more than $1000 in 2023"
4. Click **🚀 Generate Query**
5. Review the result
6. Click **✅ Keep & Apply** to insert into editor

### For Modifying Existing Query:
1. Write or have a query in editor: `SELECT * FROM users`
2. Right-click → AI Query Assistant
3. Choose mode: ✏️ **Modify Existing**
4. Enter modification: "Add filter for age > 25"
5. Generate and apply

### For Appending to Query:
1. Have a query in editor
2. Right-click → AI Query Assistant
3. Choose mode: ➕ **Append to Query**
4. Enter addition: "Also get their orders"
5. Generate and apply

## Multi-Language Support

You can enter prompts in any language:

**Tamil:**
```
2023-ல் $1000க்கு மேல் வாங்கிய வாடிக்கையாளர்களைக் காட்டு
```

**Hindi:**
```
2023 में $1000 से अधिक खरीदने वाले ग्राहकों को दिखाएं
```

**French:**
```
Afficher les clients qui ont acheté plus de 1000$ en 2023
```

## Features

✅ **Table Attachment** - Select specific tables like Cursor's file attachment
✅ **Three Modes** - New, Modify, Append
✅ **Clean Output** - SQL + Brief explanation, no fluff
✅ **Keep/Discard** - Like Cursor's code generation
✅ **Multi-language** - Works with Tamil, Hindi, French, etc.
✅ **Context-Aware** - Uses full database ER schema
✅ **Confidence Score** - Shows AI's confidence (0-100%)
✅ **Complexity Indicator** - Simple, Medium, Complex

## Troubleshooting

### "AI Not Available"
- Check API key in main.py (line 40)
- Verify internet connection

### "No Database Selected"
- Open or create a database first
- Use "📂 Open DB" button

### Empty Results
- Make sure tables are selected
- Check if database has data
- Try simpler prompts first

### JSON Errors on Startup
- Run `python fix_json_files.py` again
- Check databases folder permissions

## Advanced Tips

### 1. Table Selection Strategy
- Select **all tables** for complex queries with JOINs
- Select **specific tables** for simple queries (faster)

### 2. Prompt Engineering
- Be specific: "Show customers who bought more than $1000 **in 2023**"
- Include grouping: "Show total sales **by category**"
- Specify sorting: "Show top 10 customers **by revenue**"

### 3. Modify vs Append
- **Modify**: Change existing logic (filters, columns)
- **Append**: Add additional data (UNION, subqueries)

### 4. Optimization
- Use "🔧 AI Optimize" from right-click menu
- AI will suggest indexes, better JOINs, etc.

## Examples

### Example 1: Simple Select
```
Prompt: "Show all employees with salary > 50000"

Result:
SELECT * FROM Salaries WHERE salary > 50000

Explanation: Filters employees by salary threshold.
```

### Example 2: JOIN Query
```
Prompt: "Show customers and their total order amounts"

Result:
SELECT c.name, SUM(o.total) as total_spent
FROM customers c
LEFT JOIN orders o ON c.id = o.user_id
GROUP BY c.id, c.name

Explanation: Joins customers with orders, calculates total spent per customer.
```

### Example 3: Complex Aggregation
```
Prompt: "Show product categories with average price and count, sorted by revenue"

Result:
SELECT 
    category,
    COUNT(*) as product_count,
    AVG(price) as avg_price,
    SUM(price * quantity) as total_revenue
FROM products
GROUP BY category
ORDER BY total_revenue DESC

Explanation: Aggregates products by category with pricing metrics, sorted by revenue.
```

## Next Steps

1. Try generating simple queries first
2. Experiment with multi-language prompts
3. Use modify mode to refine queries
4. Explore the three different modes
5. Check the full guide in the artifact for advanced features

## Support

For issues or questions:
- Check the complete AI Pipeline Guide artifact
- Review the project documentation
- Check console output for detailed error messages

---

**Happy Querying!** 🚀
