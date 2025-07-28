"""Database Tools - PostgreSQL with SSH Tunnel Support"""
import os
import psycopg2
import psycopg2.extras
from sshtunnel import SSHTunnelForwarder
from typing import Dict, Any, List, Optional
from contextlib import contextmanager
from strands import tool
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class DatabaseConnection:
    """PostgreSQL connection manager with SSH tunnel support"""
    
    def __init__(self):
        self.tunnel = None
        self.connection = None
        
    def _get_env_vars(self) -> Dict[str, str]:
        """Get database configuration from environment variables"""
        required_vars = {
            'DB_HOST': os.getenv('DB_HOST'),
            'DB_PORT': int(os.getenv('DB_PORT', '5432')),
            'DB_NAME': os.getenv('DB_NAME'),
            'DB_USERNAME': os.getenv('DB_USERNAME'),
            'DB_PASSWORD': os.getenv('DB_PASSWORD'),
            'BASTION_HOST': os.getenv('BASTION_HOST'),
            'BASTION_USER': os.getenv('BASTION_USER', 'ec2-user'),
            'BASTION_PORT': int(os.getenv('BASTION_PORT', '22')),
            'SSH_KEY_PATH': os.getenv('SSH_KEY_PATH'),
            'LOCAL_PORT': int(os.getenv('LOCAL_PORT', '5432'))
        }
        
        missing_vars = [k for k, v in required_vars.items() if v is None]
        if missing_vars:
            raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")
            
        return required_vars
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connection with SSH tunnel"""
        config = self._get_env_vars()
        tunnel = None
        connection = None
        
        try:
            # Create SSH tunnel
            tunnel = SSHTunnelForwarder(
                (config['BASTION_HOST'], config['BASTION_PORT']),
                ssh_username=config['BASTION_USER'],
                ssh_pkey=config['SSH_KEY_PATH'],
                remote_bind_address=(config['DB_HOST'], config['DB_PORT']),
                local_bind_address=('localhost', config['LOCAL_PORT'])
            )
            tunnel.start()
            
            # Connect to PostgreSQL through tunnel
            connection = psycopg2.connect(
                host='localhost',
                port=config['LOCAL_PORT'],
                database=config['DB_NAME'],
                user=config['DB_USERNAME'],
                password=config['DB_PASSWORD'],
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            
            yield connection
            
        except Exception as e:
            raise Exception(f"Database connection failed: {str(e)}")
        finally:
            if connection:
                connection.close()
            if tunnel:
                tunnel.stop()


# Global database connection instance
db_manager = DatabaseConnection()


@tool
def execute_sql_query(query: str) -> Dict[str, Any]:
    """Execute SQL query on PostgreSQL database through SSH tunnel
    
    Args:
        query: SQL query to execute (SELECT only)
        
    Returns:
        Dictionary containing query results or error information
    """
    try:
        # Security check - only allow SELECT queries
        query_upper = query.strip().upper()
        if not query_upper.startswith('SELECT') and not query_upper.startswith('WITH'):
            return {
                "success": False,
                "error": "Only SELECT queries are allowed for security reasons"
            }
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                
                # Convert results to list of dictionaries
                data = [dict(row) for row in results]
                
                return {
                    "success": True,
                    "query": query,
                    "row_count": len(data),
                    "data": data[:100],  # Limit to 100 rows for performance
                    "truncated": len(data) > 100
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


@tool
def get_database_schema() -> Dict[str, Any]:
    """Get database schema information (tables, columns, types)
    
    Returns:
        Dictionary containing schema information
    """
    try:
        schema_query = """
        SELECT 
            t.table_name,
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.column_default,
            tc.constraint_type
        FROM information_schema.tables t
        LEFT JOIN information_schema.columns c ON t.table_name = c.table_name
        LEFT JOIN information_schema.key_column_usage kcu ON c.table_name = kcu.table_name 
            AND c.column_name = kcu.column_name
        LEFT JOIN information_schema.table_constraints tc ON kcu.constraint_name = tc.constraint_name
        WHERE t.table_schema = 'public' 
            AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_name, c.ordinal_position;
        """
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(schema_query)
                results = cursor.fetchall()
                
                # Organize schema by table
                schema = {}
                for row in results:
                    table_name = row['table_name']
                    if table_name not in schema:
                        schema[table_name] = {
                            'columns': [],
                            'primary_keys': [],
                            'foreign_keys': []
                        }
                    
                    if row['column_name']:  # Skip if no columns (shouldn't happen)
                        column_info = {
                            'name': row['column_name'],
                            'type': row['data_type'],
                            'nullable': row['is_nullable'] == 'YES',
                            'default': row['column_default']
                        }
                        schema[table_name]['columns'].append(column_info)
                        
                        if row['constraint_type'] == 'PRIMARY KEY':
                            schema[table_name]['primary_keys'].append(row['column_name'])
                        elif row['constraint_type'] == 'FOREIGN KEY':
                            schema[table_name]['foreign_keys'].append(row['column_name'])
                
                return {
                    "success": True,
                    "schema": schema,
                    "table_count": len(schema)
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
def get_table_list() -> Dict[str, Any]:
    """Get a simple list of all tables in the database
    
    Returns:
        Dictionary containing table names
    """
    try:
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                
                table_names = [row['table_name'] for row in results]
                
                return {
                    "success": True,
                    "tables": table_names,
                    "table_count": len(table_names)
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
def get_table_sample(table_name: str, limit: int = 5) -> Dict[str, Any]:
    """Get sample data from a specific table
    
    Args:
        table_name: Name of the table to sample
        limit: Number of rows to return (default: 5)
        
    Returns:
        Dictionary containing sample data
    """
    try:
        # Sanitize table name to prevent SQL injection
        if not table_name.replace('_', '').replace('-', '').isalnum():
            return {
                "success": False,
                "error": "Invalid table name format"
            }
        
        query = f"SELECT * FROM {table_name} LIMIT {min(limit, 10)}"
        
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                
                data = [dict(row) for row in results]
                
                return {
                    "success": True,
                    "table_name": table_name,
                    "sample_data": data,
                    "row_count": len(data)
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "table_name": table_name
        }


# Test code
if __name__ == "__main__":
    print("🧪 Database Tools Test")
    print("=" * 50)
    
    # Test schema retrieval
    print("\n📊 Schema Test:")
    schema_result = get_database_schema()
    print(f"Success: {schema_result['success']}")
    if schema_result['success']:
        print(f"Tables found: {schema_result['table_count']}")
        for table_name in list(schema_result['schema'].keys())[:3]:
            print(f"  - {table_name}")
    else:
        print(f"Error: {schema_result['error']}")
    
    # Test simple query
    print("\n🔍 Query Test:")
    query_result = execute_sql_query("SELECT version()")
    print(f"Success: {query_result['success']}")
    if query_result['success']:
        print(f"PostgreSQL Version: {query_result['data'][0] if query_result['data'] else 'N/A'}")
    else:
        print(f"Error: {query_result['error']}")
    
    print("\n" + "=" * 50)
    print("✅ Database tools test completed!")