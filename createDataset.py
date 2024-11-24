import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

class LeagueDataCollector:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "X-Riot-Token": self.api_key
        }
        self.region = "na1"
        self.region_v5 = "americas"
        
    def get_challenger_players(self):
        url = f"https://{self.region}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5"
        response = requests.get(url, headers=self.headers)
        return [entry['summonerId'] for entry in response.json()['entries']]

    def get_puuid_from_summoner_id(self, summoner_id):
        url = f"https://{self.region}.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()['puuid']
        return None

    def get_player_matches(self, puuid, count=100):
        url = f"https://{self.region_v5}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?queue=420&type=ranked&start=0&count={count}"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def get_match_details(self, match_id):
        url = f"https://{self.region_v5}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def get_champion_mastery(self, puuid, champion_id):
        url = f"https://{self.region}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/by-champion/{champion_id}"
        response = requests.get(url, headers=self.headers)
        return response.json().get('championPoints', 0) if response.status_code == 200 else 0

    def collect_data(self, num_matches=10000, save_interval=10):
        data = []
        challenger_summoner_ids = self.get_challenger_players()
        pbar = tqdm(total=num_matches, desc="Collecting matches")
        
        matches_collected = 0
        last_save = 0
        
        for summoner_id in challenger_summoner_ids:
            if matches_collected >= num_matches:
                break
                
            try:
                puuid = self.get_puuid_from_summoner_id(summoner_id)
                if not puuid:
                    continue

                matches = self.get_player_matches(puuid)
                
                for match_id in matches:
                    if matches_collected >= num_matches:
                        break
                        
                    match_data = self.get_match_details(match_id)
                    
                    match_info = {
                        'match_id': match_id,
                        'winner': 'blue' if match_data['info']['teams'][0]['win'] else 'red'
                    }
                    
                    for i, participant in enumerate(match_data['info']['participants']):
                        team = 'blue' if i < 5 else 'red'
                        position = i % 5
                        match_info[f'{team}_champion_{position}'] = participant['championId']
                        match_info[f'{team}_mastery_{position}'] = self.get_champion_mastery(
                            participant['puuid'],
                            participant['championId']
                        )
                    
                    data.append(match_info)
                    matches_collected += 1
                    pbar.update(1)

                    if matches_collected - last_save >= save_interval:
                        df_temp = pd.DataFrame(data)
                        df_temp.to_csv('league_matches_data_temp.csv', index=False)
                        last_save = matches_collected
                        
            except Exception as e:
                print(f"\nError processing player {summoner_id}: {str(e)}")
                continue
        
        pbar.close()
        return pd.DataFrame(data)

def main():
    api_key = os.getenv('RIOT_API_KEY')
    collector = LeagueDataCollector(api_key)
    
    try:
        df = collector.collect_data(num_matches=20000, save_interval=10)
        df.to_csv('league_matches_data_final.csv', index=False)
    except KeyboardInterrupt:
        print("\nScript interrupted by user. Saving collected data...")
        if 'df' in locals():
            df.to_csv('league_matches_data_interrupted.csv', index=False)
        print("Data saved. Exiting...")

if __name__ == "__main__":
    main()