import os
import csv
import requests
import time
import re
import json
from bs4 import BeautifulSoup

# Пътища и файлове
try: 
    output_dir = os.path.dirname(os.path.abspath(__file__)) 
except NameError: 
    output_dir = os.getcwd()

output_file = os.path.join(output_dir, 'ultimate_doctors_data.csv')
state_file = os.path.join(output_dir, 'state.json') # Тук пазим прогреса
base_url = "https://www.zdraveopazvaneto.bg/%D0%BB%D0%B5%D0%BA%D0%B0%D1%80%D0%B8-%D0%BF%D0%BA16.html?page="

def load_state():
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            return json.load(f).get('last_page', 1)
    return 1

def save_state(page):
    with open(state_file, 'w') as f:
        json.dump({'last_page': page}, f)

def extract_coords(soup):
    map_wrap = soup.find('div', class_='partitions_map_wrap')
    if map_wrap:
        map_link = map_wrap.find('a', href=True)
        if map_link:
            href = map_link['href']
            match = re.search(r'([-+]?\d*\.\d+),([-+]?\d*\.\d+)', href)
            if match:
                return match.group(1), match.group(2)
    return "", ""

def scrape_ultimate_doctors(): 
    start_time = time.time()
    # GitHub дава 6 часа, спираме на 5.5 (19800 сек), за да имаме време за Git Push
    TIME_LIMIT = 19800 

    print("Йо шефе, почваме голямото източване... ¡Vámonos!")
    
    current_page = load_state()
    print(f"Продължаваме от страница: {current_page}. Евала, льоло!")

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    # Проверяваме дали файлът съществува, за да знаем дали да пишем заглавия
    file_exists = os.path.exists(output_file)

    with open(output_file, mode='a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Име', 'Адрес', 'Телефон', 'Имейл', 'Отрасъл', 'Дейност', 'Ключови думи', 'Latitude', 'Longitude', 'Описание', 'Линк'])
        
        page = current_page
        while True:
            # Проверка на времето - ако стане андибул морков, спираме!
            if (time.time() - start_time) > TIME_LIMIT:
                print(f"Мамка му човече, времето изтича! Спираме на страница {page}.")
                save_state(page)
                break

            url = f"{base_url}{page}"
            print(f"Ровя в страница {page}...")
            
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code != 200:
                    print(f"Стана паприкаш на {page}. Край.")
                    save_state(page)
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                firms = soup.find_all('div', class_='box_firm_wrap')
                
                if not firms:
                    print("Свършиха палавникчовците! Мисията е успешна.")
                    save_state(1) # Рестартираме за следващия цикъл след време
                    break
                
                for firm in firms:
                    title_tag = firm.find('a', class_='title_firm')
                    firm_link = title_tag.get('href', '').strip() if title_tag else ""
                    if not firm_link: continue
                    
                    try:
                        inner_resp = requests.get(firm_link, headers=headers, timeout=15)
                        if inner_resp.status_code == 200:
                            inner_soup = BeautifulSoup(inner_resp.text, 'html.parser')
                            name_tag = inner_soup.find('div', class_='bgr1_title')
                            name = name_tag.find('h1').text.strip() if name_tag and name_tag.find('h1') else "Неизвестен"
                            
                            lat, lon = extract_coords(inner_soup)
                            # ... (тук останалият код за парсване е същият като преди)
                            
                            # Примерно записване (съкратено за краткост тук)
                            writer.writerow([name, "Адрес...", "Тел...", "Email...", "Отрасъл...", "Дейност...", "Ключове...", lat, lon, "Описание...", firm_link])
                            file.flush()
                            time.sleep(0.8)
                    except Exception as e:
                        print(f"Грешка при {firm_link}: {e}")

                page += 1
                save_state(page) # Записваме прогреса след всяка готова страница
            except Exception as e:
                print(f"Грешка на страница {page}: {e}")
                save_state(page)
                break

    print(f"До нови срещи, боклуче! ¡Adiós!")

if __name__ == "__main__":
    scrape_ultimate_doctors()
