
import logging
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


raw_users = extract_users(page_size=30)
print(raw_users)
            
