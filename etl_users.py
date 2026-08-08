
import logging
import sqlite3
from typing import Any
import requests as re



API_BASE_URL = 'https://dummyjson.com/users'
logging.basicConfig(level=logging.INFO)


logger = logging.getLogger()


#Extração de dados da API

def extract_users(page_size: int = 30) -> list[dict[str, Any]]:
    users: list[dict[str, Any]] = []
    skip = 0
    total = None

    while total is None or skip < total:
        params = {'limit': page_size, 'skip': skip}
        response = re.get(API_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        page = data["users"]
        users.extend(page)
        total = data["total"]

        logger.info(
            "Página buscada: skip=%d, total=%d, usuários extraídos=%d",
            skip, len(page), len(users)
        )
        skip += page_size

    logger.info("Extração concluída: %s usuários recebidos.", len(users))
    return users





#Criação das tabelas (DDL)


DDL = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        first_name TEXT NOT NULL,
        lastName TEXT NOT NULL,
        age INTEGER,
        gender TEXT,      
        email TEXT,
        phone TEXT,
        username TEXT,  
        birthDate TEXT,
        university TEXT);

        """,

        """
        CREATE TABLE IF NOT EXISTS address (
            user_id INTEGER PRIMARY KEY,
            address TEXT,
            city TEXT,
            state TEXT,
            stateCode TEXT,      
            postalCode  TEXT,
            country TEXT,
            lat REAL,  
            lng REAL,
            FOREIGN KEY (user_id) REFERENCES users (id));
        """,

        """
        CREATE TABLE IF NOT EXISTS company (
            user_id INTEGER PRIMARY KEY,
            department TEXT,
            name TEXT,
            title TEXT,
            city TEXT,      
            state  TEXT,
            country TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id));
        """
        ]

def create_tables(conn: sqlite3.Connection):
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS company;")
    cursor.execute("DROP TABLE IF EXISTS address;")
    cursor.execute("DROP TABLE IF EXISTS users;")

    for ddl in DDL:
        cursor.execute(ddl)
    conn.commit()
    logger.info("Tabelas criadas com sucesso.")




#Ingestão dos dados nas tabelas


def user_table(data: dict[str, Any]):
    return (
        data['id'],
        data.get('firstName'),
        data.get('lastName'),
        data.get('age'),
        data.get('gender'),
        data.get('email'),
        data.get('phone'),
        data.get('username'),
        data.get('birthDate'),
        data.get('university')
    )


def address_table(data: dict[str, Any]):
    address = data.get('address')
    coordinates = address.get('coordinates') if address else None
    return (
        data['id'],
        address.get('address') if address else None,
        address.get('city') if address else None,
        address.get('state') if address else None,
        address.get('stateCode') if address else None,
        address.get('postalCode') if address else None,
        address.get('country') if address else None,
        coordinates.get('lat') if coordinates else None,
        coordinates.get('lng') if coordinates else None
    )

def company_table(data: dict[str, Any]):
    company = data.get('company')
    address_company = company.get('address') if company else None
    return (
        data['id'],
        company.get('department') if company else None,
        company.get('name') if company else None,
        company.get('title') if company else None,
        address_company.get('city') if address_company else None,
        address_company.get('state') if address_company else None,
        address_company.get('country') if address_company else None
    )


def load_data(conn: sqlite3.Connection, users: list[dict[str, Any]]) -> None:

    user = [user_table(user) for user in users]
    address = [address_table(user) for user in users]
    company = [company_table(user) for user in users]

    cursor = conn.cursor()

    cursor.executemany(
        """
        INSERT INTO users (
            id, first_name, lastName, age, gender, email, phone, username, birthDate, university)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, user)

    cursor.executemany(
            """
            INSERT INTO address (
                user_id, address, city, state, stateCode, postalCode, country, lat, lng)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, address)

    cursor.executemany(
                """
                INSERT INTO company (
                    user_id, department, name, title, city, state, country)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, company)

    conn.commit()
    logger.info("Dados carregados com sucesso nas tabelas.")




#Orquestração do ETL

def run(path):
    raw_users = extract_users()

    conn = sqlite3.connect(path)
    try:
        create_tables(conn)
        load_data(conn, raw_users)
    except Exception as e:
        logger.exception("Erro durante a execução do ETL %s", e)
    finally:
        conn.close()
        logger.info("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    run("users.db")
