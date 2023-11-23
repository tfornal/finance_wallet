from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

username = "root"
password = "niewiem1"
database_name = "finance_wallet"

DATABASE_URL = f"mysql+pymysql://{username}:{password}@127.0.0.1:3306/{database_name}"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

if __name__ == "__main__":
    metadata = MetaData()  # creates metadata object

    with engine.connect() as connection:  # connection with datbaase
        users_table = Table("users", metadata, autoload_with=engine)
        result = connection.execute(users_table.select())
        for row in result:
            print(row)
