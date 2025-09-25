from sqlalchemy import create_engine, inspect

engine = create_engine("sqlite:///macti.db")
inspector = inspect(engine)

print("Tablas en la BD:")
print(inspector.get_table_names())

for table in inspector.get_table_names():
    print(f"\nColumnas de {table}:")
    for col in inspector.get_columns(table):
        print(col["name"], col["type"])