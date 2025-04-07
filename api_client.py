import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# URL-адреса для поиска
SEARCH_URL_LORDSERIAL = 'https://lordserial.run/index.php?do=search'
SEARCH_URL_GOODFILMS = 'https://zhcpg.goodfilms.fun/index.php?do=search'

# Глобальный кэш результатов поиска
search_results_cache = {}

async def async_get_page(url: str, params: dict = None) -> str:
    """
    Асинхронно получает HTML-код страницы по указанному URL с параметрами.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            text = await response.text()
            logger.debug(f"HTML код страницы (первые 1000 символов): {text[:1000]}")
            return text

def parse_search_results_lordserial(content: str) -> list:
    """
    Парсит HTML-код страницы с результатами поиска с сайта lordserial.
    Извлекает заголовок и ссылку.
    """
    soup = BeautifulSoup(content, 'html.parser')
    results = []
    for item in soup.find_all('div', class_='th-item'):
        title_elem = item.find('div', class_='th-title')
        title = title_elem.get_text(strip=True) if title_elem else "Без заголовка"
        link_elem = item.find('a', class_='th-in with-mask')
        link = link_elem['href'] if link_elem and link_elem.has_attr('href') else ""
        results.append((f"{title} (Источник 1)", link))
    return results

async def get_search_results_lordserial(search_term: str) -> list:
    """
    Получает результаты поиска с сайта lordserial по заданному запросу.
    """
    params = {'do': 'search', 'subaction': 'search', 'story': search_term}
    content = await async_get_page(SEARCH_URL_LORDSERIAL, params=params)
    return parse_search_results_lordserial(content)

def parse_search_results_goodfilms(content: str) -> list:
    """
    Парсит HTML-код страницы с результатами поиска с сайта goodfilms.
    Извлекает заголовок и ссылку.
    """
    soup = BeautifulSoup(content, 'html.parser')
    results = []
    for item in soup.find_all('div', class_='th-item'):
        title_elem = item.find('div', class_='th-title')
        title = title_elem.get_text(strip=True) if title_elem else "Без заголовка"
        link_elem = item.find('a', class_='th-in with-mask')
        link = link_elem['href'] if link_elem and link_elem.has_attr('href') else ""
        results.append((f"{title} (Источник 2)", link))
    return results

async def get_search_results_goodfilms(search_term: str) -> list:
    """
    Получает результаты поиска с сайта goodfilms по заданному запросу.
    """
    params = {
        'do': 'search',
        'subaction': 'search',
        'story': search_term,
        'result_from': 1
    }
    content = await async_get_page(SEARCH_URL_GOODFILMS, params=params)
    return parse_search_results_goodfilms(content)

async def search_serials(search_term: str) -> list:
    """
    Объединяет результаты поиска с двух источников.
    Результаты кэшируются для оптимизации повторных запросов.
    """
    if search_term in search_results_cache:
        logger.debug("Возвращаем кэшированные результаты")
        return search_results_cache[search_term]
    results_lordserial, results_goodfilms = await asyncio.gather(
        get_search_results_lordserial(search_term),
        get_search_results_goodfilms(search_term)
    )
    results = results_lordserial + results_goodfilms
    search_results_cache[search_term] = results
    return results

async def search_movie_async(query: str) -> str:
    """
    Асинхронно ищет фильм или сериал по заданному запросу.
    Объединяет результаты поиска с внешних источников и формирует ответ.
    """
    results = await search_serials(query)
    if not results:
        return f"Ничего не найдено для '{query}'."
    response_lines = [f"{title}: {link}" for title, link in results]
    return "\n".join(response_lines)
