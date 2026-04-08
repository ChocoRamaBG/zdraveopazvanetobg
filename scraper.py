import os
import csv
import requests
import time
import re
from bs4 import BeautifulSoup

# Магията за папката - GitHub Actions работи в специфична среда
try: 
    output_dir = os.path.dirname(os.path.abspath(__file__)) 
except NameError: 
    output_dir = os.getcwd()

output_file = os.path.join(output_dir, 'ultimate_doctors_data.csv')
base_url = "https://www.zdraveopazvaneto.bg/%D0%BB%D0%B5%D0%BA%D0%B0%D1%80%D0%B8-%D0%BF%D0%BA16.html?page="

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
    print("Йо шефе, почваме голямото източване... ¡Vámonos a la victoria!")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # Отваряме файла в 'a' (append) режим, ако искаш да не губиш инфо, 
    # но за GitHub Actions 'w' е по-добре, за да пренаписва новия отчет.
    with open(output_file, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['Име', 'Адрес', 'Телефон', 'Имейл', 'Отрасъл', 'Дейност', 'Ключови думи', 'Latitude', 'Longitude', 'Описание', 'Линк'])
        
        page = 1
        max_pages = 50 # Не бъди лаком льольо, сложи лимит да не те баннат веднага
        
        while page <= max_pages:
            url = f"{base_url}{page}"
            print(f"Ровя в главна страница {page}... ¡Qué horror!")
            
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code != 200:
                    print(f"Стана паприкаш на страница {page}! Status: {response.status_code}")
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                firms = soup.find_all('div', class_='box_firm_wrap')
                
                if not firms:
                    print("Свършиха палавникчовците на тази страница!")
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
                            name = name_tag.find('h1').text.strip() if name_tag and name_tag.find('h1') else "Неизвестен палавник"
                            
                            lat, lon = extract_coords(inner_soup)
                            
                            address, phone, email, sector, activity, keywords, description = "", "", "", "", "", "", ""
                            
                            partition_wraps = inner_soup.find_all('div', class_='w100')
                            for wrap in partition_wraps:
                                const = wrap.find('div', class_='partitions_const')
                                val = wrap.find('div', class_='partitions_value')
                                
                                if const and val:
                                    c_text = const.text.strip()
                                    if "Адрес:" in c_text:
                                        address = val.text.strip()
                                    elif "Телефони:" in c_text:
                                        phone = val.text.strip().replace(" ", "")
                                    elif "E-mail:" in c_text:
                                        email = val.text.strip()
                                    elif "Отрасъл:" in c_text:
                                        sector = val.text.strip().replace('\n', ' ').replace('\t', '')
                                    elif "Дейност:" in c_text:
                                        activity = val.text.strip()
                                    elif "Ключови думи:" in c_text:
                                        keywords = val.text.strip().replace('[виж още]', '').replace('[скрий]', '').replace('…', '').strip()
                            
                            about_div = inner_soup.find('div', class_='txt_about_us')
                            if about_div:
                                description = about_div.text.strip().replace('\n', ' ')
                            
                            writer.writerow([name, address, phone, email, sector, activity, keywords, lat, lon, description, firm_link])
                            file.flush() # Записваме веднага, че ако забие облака, да не е тотал щета
                            time.sleep(1) # Малко почивка за сървърчовците, не бъди токсичен
                            
                    except Exception as e:
                        print(f"Мамка му човече, грешка при {firm_link}: {e}")
                
                page += 1
            except Exception as e:
                print(f"Грешка при зареждане на страница {page}: {e}")
                break

    print(f"Успех, боклуче! Всичко е в {output_file}. ¡Adiós!")

if __name__ == "__main__":
    scrape_ultimate_doctors()
