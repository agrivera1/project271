from sqlalchemy import create_engine
import pandas as pd

# PostgreSQL database connection config
DB_CONFIG = {
    "dbname": '271',
    "user": 'postgres',
    "password": '123456',
    "host": 'localhost',
    "port": '5434'
}

DB_URI = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

# Fetch data
def fetch_store_data():
    """Fetches store locations from PostgreSQL, ensuring proper data formatting."""
    try:
        engine = create_engine(DB_URI)
        query = """
        SELECT store_name, 
               NULLIF(REGEXP_REPLACE(store_latitude, '[^0-9.-]', '', 'g'), '')::FLOAT AS store_latitude, 
               NULLIF(REGEXP_REPLACE(store_longitude, '[^0-9.-]', '', 'g'), '')::FLOAT AS store_longitude, 
               '7eleven' AS store_type
        FROM "7eleven"
        UNION ALL
        SELECT store_name, 
               NULLIF(REGEXP_REPLACE(store_latitude, '[^0-9.-]', '', 'g'), '')::FLOAT AS store_latitude, 
               NULLIF(REGEXP_REPLACE(store_longitude, '[^0-9.-]', '', 'g'), '')::FLOAT AS store_longitude, 
               'Jollibee' AS store_type
        FROM "Jollibee";
        """
        df = pd.read_sql(query, con=engine)

        # Drop rows with NULL values after cleaning
        df.dropna(subset=["store_latitude", "store_longitude"], inplace=True)

        print("\n✅ Successfully fetched data!")
        print(df.head())  # Debug output

        return df

    except Exception as e:
        print(f"⚠️ Database Error: {e}")
        return pd.DataFrame()  # Return empty dataframe if an error occurs

# Run fetch
if __name__ == "__main__":
    df = fetch_store_data()
