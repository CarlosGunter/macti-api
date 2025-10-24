from sqlalchemy import create_engine, inspect, text

engine = create_engine("sqlite:///macti.db")
inspector = inspect(engine)

print("Registros de la bd:")
print(inspector.get_table_names())

for table in inspector.get_table_names():
    print(f"\n Columnas de {table}:")
    for col in inspector.get_columns(table):
        print(f" - {col['name']} ({col['type']})")


    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT * FROM {table}")).fetchall()
        print(f"\n Datos en {table}:")
        if result:
            for row in result:
                print(row)
        else:
            print(" (sin registros)")
