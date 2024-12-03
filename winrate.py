import json
import requests
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
import logging

class LeagueCounterScraper:
    def __init__(self):
        self.base_url = "https://www.counterstats.net/league-of-legends/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.data = {}
        self.role_mapping = {
            "TOP": "top",
            "JUNGLE": "jungle",
            "MIDDLE": "mid",
            "BOTTOM": "adc",
            "UTILITY": "support"
        }
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('scraper.log')
            ]
        )

    def load_champions(self):
        with open('champions.json', 'r') as f:
            return json.load(f)

    def get_champion_roles(self, champion: str) -> list:
        try:
            url_champion = champion.replace(' ', '-')
            url = f"{self.base_url}{url_champion.lower()}"
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            roles = []
            role_spans = soup.find_all('span', class_='collapse')
            
            for span in role_spans:
                role_id = span.get('id', '').upper()
                for game_role, site_role in self.role_mapping.items():
                    if site_role.lower() == role_id.lower():
                        roles.append(game_role)
                        break
            
            return roles
        except Exception as e:
            logging.error(f"Error getting roles for {champion}: {e}")
            return []
    
    def get_champion_matchups(self, champion: str, role: str) -> dict:
        try:
            formatted_role = self.role_mapping[role]
            url_champion = champion.replace(' ', '-')
            url = f"{self.base_url}{url_champion.lower()}"
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            matchups = {}

            champ_boxes = soup.find_all('div', class_='champ-box__wrap new')

            target_box = None
            for box in champ_boxes:
                role_span = box.find('h2').find('span', class_='collapse')
                if role_span and role_span.get('id', '').lower() == formatted_role.lower():
                    target_box = box
                    break
            
            if not target_box:
                logging.warning(f"Could not find matchup data for {champion} {role}")
                return {}
                
            matchup_rows = target_box.select('a.champ-box__row')
            
            for row in matchup_rows:
                try:
                    champion_element = row.select_one('div.win-wrap span.champion')

                    winrate_element = row.select_one('div.win-wrap span.win span.b')
                    
                    if champion_element and winrate_element:
                        opponent_name = champion_element.text.strip()
                        opponent_name = opponent_name.replace(' ', '').replace("'", '').lower()
                        winrate_text = winrate_element.text.strip().rstrip('%')
                        
                        try:
                            winrate = 100 - float(winrate_text)
                            matchups[opponent_name] = winrate
                        except ValueError:
                            logging.warning(f"Could not convert winrate '{winrate_text}' to float for {opponent_name}")
                            continue
                            
                except Exception as e:
                    logging.warning(f"Error processing matchup row: {e}")
                    continue
            
            if not matchups:
                logging.warning(f"No matchups found for {champion} {role}")
                
            return matchups
            
        except Exception as e:
            logging.error(f"Error getting matchups for {champion} {role}: {e}")
            return {}

    def get_champion_roles(self, champion: str) -> list:
        try:
            url_champion = champion.replace(' ', '-')
            url = f"{self.base_url}{url_champion.lower()}"
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            roles = []
            role_spans = soup.find_all('span', class_='collapse')
            
            for span in role_spans:
                role_id = span.get('id', '').upper()
                for game_role, site_role in self.role_mapping.items():
                    if site_role.lower() == role_id.lower():
                        roles.append(game_role)
                        break
            
            return roles
        except Exception as e:
            logging.error(f"Error getting roles for {champion}: {e}")
            return []

    def scrape_all_data(self):
        logging.basicConfig(level=logging.INFO)
        champions = self.load_champions()
        
        for champion in tqdm(champions):
            if champion["id"] == "none":
                continue
                
            logging.info(f"Processing {champion['id']}...")
            formatted_champion_id = champion['id'].replace(' ', '').replace("'", '').lower()
            if(formatted_champion_id not in self.data):
                self.data[formatted_champion_id] = {}
            
            roles = self.get_champion_roles(champion['id'])
            
            if not roles:
                logging.warning(f"No roles found for {champion['id']}")
                continue
            
            for role in roles:
                logging.info(f"Getting matchups for {champion['id']} {role}...")
                try:
                    matchups = self.get_champion_matchups(champion['id'], role)
                    self.data[formatted_champion_id][role] = matchups
                    self.save_to_json("matchups_backup.json")
                except Exception as e:
                    logging.exception(f"Error processing {champion['id']} {role}")
                    print(f"Error: {str(e)}")
                    print("Full traceback:")
                    import traceback
                    traceback.print_exc()
                    exit(1)


    def save_to_json(self, filename: str = "league_matchups.json"):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
            logging.info(f"Data successfully saved to {filename}")
        except Exception as e:
            logging.error(f"Error saving data to JSON: {e}")

def main():
    scraper = LeagueCounterScraper()
    scraper.scrape_all_data()
    scraper.save_to_json()

if __name__ == "__main__":
    main()