# 🚀 MariaDB: Aries Edition

**A Powerful SQL Compiler & AI-Enhanced Database Management System**

Welcome to **MariaDB: Aries Edition** - a cutting-edge database management workbench that combines powerful SQL compilation capabilities with intelligent AI assistance. Built by our dedicated team, Aries Edition makes database management intuitive, efficient, and accessible to everyone, from beginners to database experts.

---

## ✨ What Makes Aries Edition Special?

**MariaDB: Aries Edition** isn't just another database tool - it's a complete solution that bridges the gap between standard SQL dialects and SQLite, while supercharging your workflow with AI-powered features. Whether you're working with MySQL, PostgreSQL, SQL Server, or Oracle syntax, our intelligent SQL compiler handles the translation automatically.

### Why "Aries Edition"?

Just like the Aries constellation lights up the database sky, this edition brings clarity and intelligence to your database operations. Our team has crafted an experience that's both powerful for professionals and friendly for newcomers.

---

## 🎯 Key Features at a Glance

### 🔧 Intelligent SQL Compiler
Transform SQL from any major database system into SQLite-compatible syntax automatically.

### 🤖 AI-Powered Query Generation
Generate perfect SQL queries from natural language - supports multiple languages including English, Tamil, Hindi, French, and more!

### 📊 AI Dashboard & Visualization
Automatically analyze query results and suggest optimal visualizations for your data.

### 📝 Smart Query Builder
Build complex queries visually with our intuitive drag-and-drop interface.

### 🗂️ Schema Visualizer
Understand your database structure at a glance with beautiful visual representations.

### ⭐ Query History & Favorites
Never lose your work - track every query and save your favorites for quick access.

---

## 🔧 SQL Compiler Functionality

### Overview

The **SQL Compiler** in Aries Edition is our flagship feature that makes database portability effortless. It intelligently converts SQL syntax from various database systems into SQLite-compatible code, handling type conversions, function mappings, and syntax differences automatically.

### Supported SQL Dialects

- **MySQL** (VARCHAR, AUTO_INCREMENT, etc.)
- **PostgreSQL** (SERIAL, CHARACTER VARYING, etc.)
- **SQL Server** (NVARCHAR, BIGINT, etc.)
- **Oracle** (NUMBER, LONG, CLOB, etc.)
- **Standard SQL** (Universal compatibility)

### How It Works

1. **Type Mapping**: Automatically converts data types from source dialects to SQLite equivalents
2. **Function Translation**: Maps database-specific functions to SQLite-compatible ones
3. **Syntax Normalization**: Handles CREATE TABLE, INSERT, SELECT, UPDATE, DELETE statements
4. **Constraint Handling**: Preserves PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL constraints
5. **Comment Removal**: Cleans SQL comments while preserving functionality

### Compiler Features

#### Automatic Type Conversion

```sql
-- MySQL Syntax (Input)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    salary DECIMAL(10,2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Compiled SQLite Syntax (Output)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    salary REAL,
    created_at TEXT DEFAULT (datetime('now'))
);
```

#### Function Translation

```sql
-- Standard SQL (Input)
SELECT NOW(), CURRENT_DATE, UPPER(name) 
FROM users;

-- Compiled SQLite Syntax (Output)
SELECT datetime('now'), date('now'), UPPER(name) 
FROM users;
```

#### CREATE OR REPLACE Support

```sql
-- PostgreSQL Syntax (Input)
CREATE OR REPLACE VIEW active_users AS
SELECT * FROM users WHERE status = 'active';

-- Compiled SQLite Syntax (Output)
-- Drops existing view if exists, then creates new one
DROP VIEW IF EXISTS active_users;
CREATE VIEW active_users AS
SELECT * FROM users WHERE status = 'active';
```

#### Multi-Statement Support

The compiler handles complex statements with multiple operations, preserving transaction integrity:

```sql
-- Input: Mixed MySQL syntax
CREATE TABLE orders (
    order_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    total DECIMAL(10,2),
    order_date DATE
);

INSERT INTO orders (user_id, total, order_date) 
VALUES (1, 99.99, '2024-01-15');

-- Compiled: SQLite-compatible
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    total REAL,
    order_date TEXT
);

INSERT INTO orders (user_id, total, order_date) 
VALUES (1, 99.99, '2024-01-15');
```

### Using the Compiler

1. **In SQL Editor**: Type or paste your SQL from any database system
2. **Automatic Compilation**: The compiler automatically processes queries before execution
3. **Preview Compiled SQL**: Right-click → "Compile SQL" to see the converted syntax
4. **Validation**: Built-in validation ensures compiled SQL is syntactically correct

### Supported Data Types

| Source Type | SQLite Type | Notes |
|-------------|-------------|-------|
| VARCHAR(n) | TEXT | All string types unified |
| CHAR(n) | TEXT | Fixed-length becomes TEXT |
| INT, INTEGER | INTEGER | All integer variants |
| BIGINT | INTEGER | 64-bit integers |
| DECIMAL, NUMERIC | REAL | Floating-point numbers |
| FLOAT, DOUBLE | REAL | Floating-point precision |
| DATE | TEXT | ISO-8601 format |
| DATETIME | TEXT | ISO-8601 format |
| TIMESTAMP | TEXT | ISO-8601 format |
| BOOLEAN | INTEGER | 0 or 1 |
| BLOB | BLOB | Binary data preserved |

---

## 🤖 AI Functionality Explained

Aries Edition comes with a comprehensive AI suite powered by Google's Gemini, designed to make database management intuitive and accessible. Here's how each AI feature works:

### 1. AI Query Generation

**Generate SQL from Natural Language**

Simply describe what you want, and AI generates the perfect SQL query for you. It understands context, relationships, and can work with multiple languages.

**Example Usage:**

```
User Prompt: "Show me all customers who spent more than $1000 last month"
```

**AI Response:**
```sql
SELECT c.*, SUM(o.total) as total_spent
FROM customers c
INNER JOIN orders o ON c.id = o.customer_id
WHERE o.order_date >= date('now', '-1 month')
GROUP BY c.id
HAVING SUM(o.total) > 1000
ORDER BY total_spent DESC;

-- Explanation: Joins customers with orders, filters by last month, 
-- groups by customer, and shows only those with total > $1000
```

**Multi-Language Support:**

```
Tamil: "2023-ல் $1000க்கு மேல் வாங்கிய வாடிக்கையாளர்களைக் காட்டு"
Hindi: "2023 में $1000 से अधिक खरीदने वाले ग्राहकों को दिखाएं"
French: "Afficher les clients qui ont acheté plus de 1000$ en 2023"
```

All produce the same accurate SQL result!

### 2. AI Query Modification

**Refine Existing Queries Intelligently**

Already have a query? Ask AI to modify it:

```
Current Query: SELECT * FROM users

AI Prompt: "Add filter for age > 25 and sort by name"

Result: SELECT * FROM users WHERE age > 25 ORDER BY name
```

### 3. AI Query Optimization

**Make Your Queries Faster**

AI analyzes your queries and suggests optimizations:

- Index recommendations
- JOIN optimization
- Subquery improvements
- Performance tuning

```
Original: SELECT * FROM orders WHERE customer_id IN 
          (SELECT id FROM customers WHERE status = 'active')

Optimized: SELECT o.* FROM orders o
           INNER JOIN customers c ON o.customer_id = c.id
           WHERE c.status = 'active'
           
-- Explanation: Replaced subquery with JOIN for better performance
```

### 4. AI Query Explanation

**Understand Complex Queries Instantly**

Get detailed explanations of what any SQL query does:

```
Query: SELECT c.name, COUNT(o.id) as order_count
       FROM customers c
       LEFT JOIN orders o ON c.id = o.customer_id
       GROUP BY c.id, c.name;

AI Explanation: "This query retrieves all customers along with their 
total order count. It uses a LEFT JOIN to include customers who have 
no orders (showing 0), and groups results by customer ID and name to 
aggregate order counts per customer."
```

### 5. AI Dashboard Analyzer

**Automatic Data Visualization**

After running a query, AI analyzes the results and suggests optimal visualizations:

**Features:**
- **Automatic Chart Detection**: Identifies trends, distributions, and relationships
- **Multiple Chart Types**: Line, Bar, Pie, Scatter, Heatmap, Histogram, Boxplot
- **Smart Recommendations**: Suggests 4-10 visualizations based on data structure
- **Custom Instructions**: Guide AI on what visualizations you need

**Example:**

```
Query Result: Sales data by month and region

AI Suggestions:
1. Line Chart: Sales trend over time
2. Bar Chart: Sales by region comparison
3. Pie Chart: Region distribution
4. Heatmap: Month vs Region sales matrix
5. Scatter Plot: Sales vs Growth correlation
```

### 6. AI Schema Understanding

**Context-Aware Intelligence**

The AI system understands your entire database structure:

- **Full Schema Awareness**: Knows all tables, columns, and relationships
- **Table Selection**: Attach specific tables for focused query generation
- **Relationship Detection**: Understands foreign keys and JOIN opportunities
- **Sample Data Analysis**: Uses actual data patterns to improve suggestions

### 7. AI Conversation Context

**Remember Your Workflow**

The AI maintains conversation context:

- **Session Management**: Tracks ongoing conversations
- **Query History**: Remembers previous queries in the session
- **Context Preservation**: Builds on previous interactions
- **Multi-turn Refinement**: Iteratively improve queries through conversation

**Example Workflow:**

```
User: "Show me customer orders"
AI: [Generates query with customer and orders JOIN]

User: "Add total spent per customer"
AI: [Modifies query to include SUM aggregation]

User: "Only show customers with > 10 orders"
AI: [Adds HAVING clause with order count filter]
```

### 8. AI Confidence Scoring

**Know How Sure AI Is**

Every AI-generated query includes:
- **Confidence Score**: 0-100% indicating AI's certainty
- **Complexity Rating**: Simple, Medium, or Complex query classification
- **Error Probability**: Estimated risk assessment

---

## 👥 User-Friendly Features

### Intuitive Interface

**Modern, Clean Design**
- VS Code-inspired sidebar for easy navigation
- Tabbed interface for organized workflow
- Resizable panels for custom layouts
- Beautiful light theme optimized for long sessions

### Smart Shortcuts

**Work Faster with Keyboard Shortcuts**

- `Ctrl+R` - Run query instantly
- `Ctrl+G` - Generate SQL with AI
- `Ctrl+Shift+A` - Open AI chat assistant
- `Ctrl+C` - Clear editor
- `Ctrl+1-7` - Switch between tabs quickly

### Query Builder

**Visual Query Construction**

Build complex queries without writing SQL:
- Drag-and-drop table selection
- Visual JOIN builder
- Filter and condition builder
- Column selector with preview
- Real-time SQL preview

### Query History

**Never Lose Your Work**

- **Automatic Tracking**: Every query is saved automatically
- **Searchable History**: Find queries quickly
- **Success/Failure Tracking**: See which queries worked
- **Execution Time**: Monitor performance
- **One-Click Reuse**: Click to reload any previous query

### Schema Explorer

**Understand Your Database**

- **Tree View**: Browse tables, columns, indexes
- **Quick Actions**: Right-click to run common queries
- **Table Info**: View structure, row counts, sample data
- **Refresh**: Keep schema up-to-date automatically

### Session Management

**Save and Restore Your Work**

- **Save Sessions**: Save complete workspace state
- **Load Sessions**: Restore databases, queries, and settings
- **Multiple Sessions**: Switch between different projects
- **Auto-Recovery**: Automatic backup of your work

### Data Export/Import

**Work with External Data**

- **Export Formats**: CSV, JSON, SQL
- **Import Support**: Bring data from CSV/JSON
- **Backup/Restore**: Full database backup functionality
- **Selective Export**: Export specific tables or queries

---

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone or Download** the repository:
```bash
git clone <repository-url>
cd Aries_MARIA_DB
```

2. **Install Dependencies**:
```bash
pip install -r backend/requirements.txt
```

3. **Set Up API Key** (Optional for AI features):
   - Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
   - Open Settings → API Keys in the application
   - Add your API key

4. **Run the Application**:
```bash
python main.py
```

### First Steps

1. **Create or Open a Database**
   - Click "Create Database" or "Open Database" from the sidebar
   - Or use File → New Database / Open Database

2. **Try SQL Compilation**
   - Type a MySQL/PostgreSQL query in the SQL Editor
   - Click "Run Query" - it compiles automatically!

3. **Try AI Query Generation**
   - Right-click in SQL Editor → "🤖 AI Query Assistant"
   - Enter: "Show me all tables"
   - Watch AI generate the query!

4. **Explore Schema**
   - Switch to "🗂️ Schema" tab
   - Visualize your database structure

---

## 📖 Detailed Examples

### Example 1: Porting MySQL to SQLite

**Scenario**: You have a MySQL database and need to use it in SQLite.

```sql
-- Original MySQL Schema
CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- In Aries Edition: Just paste and run!
-- Automatically compiled to:
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL,
    description TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

### Example 2: AI Query Generation

**Scenario**: You want to find the top 10 customers by revenue.

```
Step 1: Open AI Query Assistant (Ctrl+Shift+A)
Step 2: Select "customers" and "orders" tables
Step 3: Enter prompt: "Show top 10 customers by total revenue"
Step 4: AI generates:
```

```sql
SELECT 
    c.id,
    c.name,
    c.email,
    SUM(o.total) as total_revenue
FROM customers c
INNER JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name, c.email
ORDER BY total_revenue DESC
LIMIT 10;

-- Confidence: 95%
-- Complexity: Medium
```

### Example 3: Complex Multi-Table Query

**Scenario**: You need sales data with customer and product information.

```
AI Prompt: "Show monthly sales with customer names and product names, 
filter for last 6 months, group by month and customer"

AI Generated Query:
```

```sql
SELECT 
    strftime('%Y-%m', o.order_date) as month,
    c.name as customer_name,
    p.name as product_name,
    SUM(oi.quantity * oi.price) as monthly_sales
FROM orders o
INNER JOIN customers c ON o.customer_id = c.id
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN products p ON oi.product_id = p.id
WHERE o.order_date >= date('now', '-6 months')
GROUP BY month, c.name, p.name
ORDER BY month DESC, monthly_sales DESC;
```

### Example 4: Query Optimization

**Scenario**: Your query is slow, need optimization.

```
Original Query:
SELECT * FROM orders WHERE customer_id IN 
(SELECT id FROM customers WHERE status = 'active' AND city = 'NYC');

AI Optimization Suggestion:
```

```sql
-- Optimized version
SELECT o.* 
FROM orders o
INNER JOIN customers c ON o.customer_id = c.id
WHERE c.status = 'active' AND c.city = 'NYC';

-- Performance Improvement: ~3x faster
-- Recommendation: Add index on customers(status, city)
```

### Example 5: AI Dashboard Visualization

**Scenario**: You want to visualize sales trends.

```
1. Run query: SELECT order_date, SUM(total) as daily_sales 
              FROM orders GROUP BY order_date ORDER BY order_date;

2. Switch to "📊 AI Dashboard" tab

3. AI automatically suggests:
   - Line Chart: Sales trend over time
   - Bar Chart: Daily sales comparison
   - Histogram: Sales distribution
   - Heatmap: Sales by day of week
   
4. Click any suggestion to generate the chart!
```

---

## 🛠️ Advanced Features

### SQL Compiler Advanced Options

- **Type Mapping Customization**: Customize how types are converted
- **Function Aliasing**: Add custom function mappings
- **Strict Mode**: Warn about potential data loss during conversion
- **Preview Mode**: See compiled SQL without executing

### AI Customization

- **Temperature Control**: Adjust AI creativity (Settings → AI)
- **Model Selection**: Choose different AI models
- **Context Window**: Configure how much schema context to use
- **Language Preference**: Set default language for prompts

### Performance Optimization

- **Query Caching**: Cache frequently used queries
- **Connection Pooling**: Efficient database connections
- **Lazy Loading**: Load schema on-demand
- **Background Processing**: Non-blocking AI operations

---

## 🎨 User Interface Overview

### Main Tabs

1. **SQL Editor** - Primary workspace for writing and executing queries
2. **Query Builder** - Visual query construction tool
3. **📜 History** - Query history and execution log
4. **⭐ Favorites** - Saved favorite queries
5. **🗂️ Schema** - Database schema visualization
6. **📊 AI Dashboard** - AI-powered data visualization
7. **⚙️ Settings** - Application configuration

### Sidebar Features

- **Database Explorer**: Browse all databases
- **Quick Actions**: Create/open databases, tables
- **Table Navigator**: Jump to specific tables
- **Context Menu**: Right-click for quick SQL actions

---

## 📚 Documentation

### SQL Compiler

- **Type Mappings**: See all supported type conversions
- **Function Reference**: Available SQL functions
- **Syntax Guide**: Supported SQL syntax features
- **Limitations**: Known limitations and workarounds

### AI Features

- **Prompt Engineering**: Tips for better AI queries
- **Multi-language Guide**: Using AI in different languages
- **Context Management**: How to use schema context effectively
- **Troubleshooting**: Common AI issues and solutions

---

## 🔒 Security & Privacy

- **Local Processing**: All data stays on your machine
- **API Key Encryption**: Secure storage of API credentials
- **No Data Collection**: We don't collect or transmit your data
- **Offline Mode**: Works without internet (AI features require API key)

---

## 🐛 Troubleshooting

### SQL Compiler Issues

**Problem**: Query not compiling correctly
- **Solution**: Check if all syntax is supported, use "Compile SQL" to preview conversion

**Problem**: Type conversion errors
- **Solution**: Check type mappings in Settings → SQL Compiler

### AI Features Not Working

**Problem**: "AI Not Available" error
- **Solution**: 
  1. Check API key in Settings → API Keys
  2. Verify internet connection
  3. Ensure API key is valid and has quota

**Problem**: AI generates incorrect queries
- **Solution**: 
  1. Provide more context by selecting relevant tables
  2. Be more specific in your prompt
  3. Use "Modify Existing" mode to refine queries

### General Issues

**Problem**: Application crashes on startup
- **Solution**: Run `python fix_json_files.py` to fix corrupted JSON files

**Problem**: Database won't open
- **Solution**: Check file permissions, ensure database isn't locked

---

## 🤝 Contributing

We welcome contributions! This is a team project and we're always looking to improve. Areas where help is especially welcome:

- Additional SQL dialect support
- New visualization types
- UI/UX improvements
- Documentation improvements
- Bug fixes and testing

---

## 📄 License

This project is developed by our team for the database management community.

---

## 🙏 Acknowledgments

Built with:
- **Python** & **Tkinter** - Core application framework
- **ttkbootstrap** - Modern UI components
- **SQLite** - Database engine
- **Google Gemini AI** - AI-powered features
- **matplotlib** - Data visualization

---

## 📞 Support

For issues, questions, or suggestions:
- Check the [Quick Start Guide](QUICKSTART.md)
- Review the troubleshooting section
- Examine console output for detailed error messages

---

## 🎯 Future Roadmap

We're constantly improving! Upcoming features:

- [ ] Additional SQL dialect support (DB2, Teradata)
- [ ] Collaborative query sharing
- [ ] Query performance profiler
- [ ] Advanced data transformation tools
- [ ] Cloud database connections
- [ ] Query templates library
- [ ] Enhanced visualization options

---

**Built with ❤️ by the Aries Team**

*Making database management accessible, intelligent, and powerful for everyone.*

---

*Version: Aries Edition 1.0*  
*Last Updated: 2025*
