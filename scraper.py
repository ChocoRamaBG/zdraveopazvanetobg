import os
import csv
import requests
import time
import re
import json
from bs4 import BeautifulSoup

# Пътища и файлчовци
try: 
    output_dir = os.path.dirname(os.path.abspath(__file__)) 
except NameError: 
    output_dir = os.getcwd()

output_file = os.path.join(output_dir, 'ultimate_doctors_data.csv')
state_file = os.path.join(output_dir, 'state.json')

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

# Тук магията реално вади данните, за да не си аджамия
def get_partition_value(soup, keyword):
    elem = soup.find('div', class_='partitions_const', string=re.compile(keyword))
    if elem:
        val = elem.find_next_sibling('div', class_='partitions_value')
        if val:
            # Махаме тъпите експандъри
            return val.get_text(separator=' ', strip=True).replace('[виж още]', '').replace('[скрий]', '').strip()
    return ""

def scrape_ultimate_doctors(): 
    start_time = time.time()
    TIME_LIMIT = 19800 

    print("Йо шефе, почваме голямото източване... ¡Vámonos!")
    
    current_page = load_state()
    
    # ФИКС ЗА БЕЗКРАЙНИЯ ЦИКЪЛ: Ако сме приключили, просто си почиваме
    if current_page == "DONE":
        print("Мамка му човече, вече сме източили всичко! Няма какво да стържем. Мисията е приключена.")
        return

    print(f"Продължаваме от страница: {current_page}. Евала, льольо!")

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    file_exists = os.path.exists(output_file)

    with open(output_file, mode='a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Име', 'Адрес', 'Телефон', 'Имейл', 'Отрасъл', 'Дейност', 'Ключови думи', 'Latitude', 'Longitude', 'Описание', 'Линк'])
        
        page = int(current_page)
        while True:
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
                    save_state("DONE") # <--- ФИКСА: Вече не връщаме на 1, а пишем DONE
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
                            
                            address = get_partition_value(inner_soup, 'Адрес')
                            phone = get_partition_value(inner_soup, 'Телефон')
                            
                            # ФИКС ЗА ТЕЛЕФОНЧОВЦИТЕ: Екселчето ще го чете като стринг и няма да яде нулите
                            if phone:
                                phone = f'="{phone}"'

                            email = get_partition_value(inner_soup, 'E-mail')
                            industry = get_partition_value(inner_soup, 'Отрасъл')
                            activity = get_partition_value(inner_soup, 'Дейност')
                            keywords = get_partition_value(inner_soup, 'Ключови думи')
                            
                            desc_div = inner_soup.find('div', class_='txt_about_us')
                            description = desc_div.get_text(separator=' ', strip=True) if desc_div else ""
                            
                            lat, lon = extract_coords(inner_soup)
                            
                            writer.writerow([name, address, phone, email, industry, activity, keywords, lat, lon, description, firm_link])
                            file.flush()
                            time.sleep(0.8)
                    except Exception as e:
                        print(f"Грешка при {firm_link}: {e}")

                page += 1
                save_state(page) 
            except Exception as e:
                print(f"Грешка на страница {page}: {e}")
                save_state(page)
                break

    print(f"До нови срещи, боклуче! ¡Adiós!")

if __name__ == "__main__":
    scrape_ultimate_doctors()
