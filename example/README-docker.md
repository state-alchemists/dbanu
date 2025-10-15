# DBAnu Docker Compose Setup

This Docker Compose setup provides PostgreSQL, MySQL, and Impala databases with pre-seeded book data for testing the DBAnu library.

## Services

### PostgreSQL
- **Port**: 5432
- **Database**: dbanu_db
- **Username**: dbanu_user
- **Password**: dbanu_password
- **Pre-seeded Data**: Books table with 5 sample records

### MySQL
- **Port**: 3306
- **Database**: dbanu_db
- **Username**: dbanu_user
- **Password**: dbanu_password
- **Root Password**: root_password
- **Pre-seeded Data**: Books table with 5 sample records

### Impala
- **Ports**: 21000, 21050, 25000, 25010, 25020
- **Database**: dbanu_db
- **Pre-seeded Data**: Books table with 5 sample records

## Quick Start

1. **Start all services**:
   ```bash
   cd example
   docker-compose up -d
   ```

2. **Check service status**:
   ```bash
   docker-compose ps
   ```

3. **Stop services**:
   ```bash
   docker-compose down
   ```

4. **Stop and remove volumes**:
   ```bash
   docker-compose down -v
   ```

## Connecting to Databases

### PostgreSQL
```bash
docker exec -it dbanu_postgres psql -U dbanu_user -d dbanu_db
```

### MySQL
```bash
docker exec -it dbanu_mysql mysql -u dbanu_user -p dbanu_db
```

### Impala
```bash
docker exec -it dbanu_impala impala-shell
```

## Sample Queries

Once connected, you can run queries like:

```sql
-- Get all books
SELECT * FROM books;

-- Get books by author
SELECT * FROM books WHERE author = 'George Orwell';

-- Get books published after 1950
SELECT * FROM books WHERE year > 1950;
```

## Data Schema

The books table has the following structure:
- `id` (INTEGER/SERIAL/AUTO_INCREMENT): Primary key
- `title` (TEXT/VARCHAR): Book title
- `author` (TEXT/VARCHAR): Author name
- `year` (INTEGER): Publication year

## Sample Data

1. "The Great Gatsby" by F. Scott Fitzgerald (1925)
2. "To Kill a Mockingbird" by Harper Lee (1960)
3. "1984" by George Orwell (1949)
4. "Pride and Prejudice" by Jane Austen (1813)
5. "The Catcher in the Rye" by J.D. Salinger (1951)