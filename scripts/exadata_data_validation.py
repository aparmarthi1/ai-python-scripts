import oracledb

def validate_table_counts(source_dsn, target_dsn, table_name, user, password):
    """
    Validate row counts between source and target Oracle Exadata databases.
    Args:
        source_dsn (str): DSN for the source database (e.g., 'source_host:1521/service_name').
        target_dsn (str): DSN for the target database (e.g., 'azure_exadata_host:1521/service_name').
        table_name (str): Name of the table to validate.
        user (str): Database username.
        password (str): Database password.
    Returns:
        tuple: Source and target row counts, or None if an error occurs.
    """
    try:
        # Connect to source database
        src_conn = oracledb.connect(user=user, password=password, dsn=source_dsn)
        src_cursor = src_conn.cursor()
        
        # Connect to target database
        tgt_conn = oracledb.connect(user=user, password=password, dsn=target_dsn)
        tgt_cursor = tgt_conn.cursor()
        
        # Get row counts
        src_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        tgt_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        src_count = src_cursor.fetchone()[0]
        tgt_count = tgt_cursor.fetchone()[0]
        
        # Close connections
        src_cursor.close()
        tgt_cursor.close()
        src_conn.close()
        tgt_conn.close()
        
        print(f"Source count for {table_name}: {src_count}")
        print(f"Target count for {table_name}: {tgt_count}")
        return src_count, tgt_count
    
    except oracledb.Error as e:
        print(f"Database error: {e}")
        return None, None

if __name__ == "__main__":
    # Example usage
    source_dsn = "source_exadata_host:1521/source_service"
    target_dsn = "azure_exadata_host:1521/target_service"
    table_name = "my_table"
    user = "admin"
    password = "password"
    
    src_count, tgt_count = validate_table_counts(source_dsn, target_dsn, table_name, user, password)
    if src_count is not None and tgt_count is not None:
        print(f"Validation {'successful' if src_count == tgt_count else 'failed'}: Source={src_count}, Target={tgt_count}")
