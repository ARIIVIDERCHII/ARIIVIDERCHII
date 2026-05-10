import requests
import json
import os 

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USERNAME = "ARIIVIDERCHII"

graphql_query = """
query($userName: String!) {
  user(login: $userName) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            color
          }
        }
      }
    }
  }
}
"""

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

variables = {
    "userName": USERNAME
}

response = requests.post(
    "https://api.github.com/graphql",
    headers=headers,
    json={"query": graphql_query, "variables": variables}
)

if response.status_code == 200:
    data = response.json()
    
    calendar = data['data']['user']['contributionsCollection']['contributionCalendar']
    print(f"Успешно! Всего контрибуций за год: {calendar['totalContributions']}")
    
    with open("contributions.json", "w", encoding="utf-8") as f:
        json.dump(calendar, f, indent=4)
        
    print("Карта уровня сохранена в файл contributions.json")
else:
    print(f"Ошибка запроса: {response.status_code}")
    print(response.text)