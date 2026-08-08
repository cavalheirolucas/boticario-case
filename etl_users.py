
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


raw_users = extract_users()
#print(raw_users)
            


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

    for ddl in DDL:
        cursor.execute(ddl)
    conn.commit()
    logger.info("Tabelas criadas com sucesso.")




#Ingestão dos dados nas tabelas


def user_table(data: dict[str, Any]):
    return (
        data['id'],
        data['firstName'],
        data['lastName'],
        data['age'],
        data['gender'],
        data['email'],
        data['phone'],
        data['username'],
        data['birthDate'],
        data['university']
    )


def address_table(data: dict[str, Any]):
    address = data.get('address')
    coordinates = address.get('coordinates')
    return (
        data['id'],
        address.get('address'),
        address.get('city'),
        address.get('state'),
        address.get('stateCode'),
        address.get('postalCode'),
        address.get('country'),
        coordinates.get('lat'),
        coordinates.get('lng')
    )

def company_table(data: dict[str, Any]):
    company = data.get('company')
    address_company = company.get('address')
    return (
        data['id'],
        company.get('department'),
        company.get('name'),
        company.get('title'),
        address_company.get('city'),
        address_company.get('state'),
        address_company.get('country')
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



    
connection = sqlite3.connect("users.db")
create_tables(connection)
load_data(connection, raw_users)
connection.close()

