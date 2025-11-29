import re
import sys

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tabulate import tabulate


def scrape_race_results(url):
    """
    指定されたURLからレース結果をスクレイピングし、レース場、レースレベル、各レースの組番を抽出します。

    Args:
        url (str): スクレイピング対象のURL。

    Returns:
        list: レース結果を格納した辞書のリスト。
              各辞書には、'race_course', 'race_grade', 'race_number', 'winning_number' のキーが含まれます。
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")

        results = []
        tables = soup.find_all("div", class_="table1")

        for table in tables:
            # Get venues and grades from table header
            header_cells = table.select('thead > tr:first-child > th[colspan="3"]')
            venues = []
            for cell in header_cells:
                name_img = cell.find("img")
                name = name_img["alt"] if name_img else "N/A"

                grade_p = cell.find("p", class_=re.compile(r"is-grade"))
                grade = "一般"  # Default grade
                if grade_p and grade_p.get("class"):
                    classes = grade_p.get("class")
                    for c in classes:
                        if c.startswith("is-G"):
                            grade = c.replace("is-", "").upper()
                            if grade.endswith("B"):
                                grade = grade[:-1]
                            break
                        elif c == "is-ippan":
                            grade = "一般"
                            break
                venues.append({"name": name, "grade": grade})

            # Get race data from table body
            race_rows = table.find_all("tbody")
            for row in race_rows:
                race_num_th = row.find("th")
                if not race_num_th:
                    continue
                race_number = race_num_th.text.strip().replace("R", "")

                payout_cells = row.find_all("td")

                # cells are grouped by 3 for each venue (combination, trifecta_payout, popularity)
                for i in range(0, len(payout_cells), 3):
                    venue_index = i // 3
                    if venue_index >= len(venues):
                        continue

                    venue_info = venues[venue_index]

                    combination_cell = payout_cells[i]
                    popularity_cell = payout_cells[i + 2]

                    if "レース中止" in combination_cell.text:
                        winning_number = "レース中止"
                        popularity = ""
                    else:
                        number_spans = combination_cell.select(".numberSet1_row span")
                        winning_number = "".join([span.text for span in number_spans])
                        popularity = popularity_cell.text.strip()

                    results.append(
                        {
                            "レース場": venue_info["name"],
                            "グレード": venue_info["grade"],
                            "レース番号": race_number,
                            "三連単": winning_number,
                            "人気": popularity,
                        }
                    )

        return results

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scrape_race_results.py <YYYY-MM-DD>")
        sys.exit(1)

    date_str = sys.argv[1].replace("-", "")  # Remove hyphens if present

    target_url = f"https://www.boatrace.jp/owpc/pc/race/pay?hd={date_str}"
    race_data = scrape_race_results(target_url)

    track_mapping = {
        "桐生": 1,
        "戸田": 2,
        "江戸川": 3,
        "平和島": 4,
        "多摩川": 5,
        "浜名湖": 6,
        "蒲郡": 7,
        "常滑": 8,
        "津": 9,
        "三国": 10,
        "びわこ": 11,
        "住之江": 12,
        "尼崎": 13,
        "鳴門": 14,
        "丸亀": 15,
        "児島": 16,
        "宮島": 17,
        "徳山": 18,
        "下関": 19,
        "若松": 20,
        "芦屋": 21,
        "福岡": 22,
        "唐津": 23,
        "大村": 24,
    }

    if race_data:
        df = pd.DataFrame(race_data)
        df["レース場"] = df["レース場"].map(track_mapping)
        df["レース番号"] = df["レース番号"].astype(int)
        df = df.sort_values(by=["レース場", "レース番号"]).reset_index(drop=True)
        print("=== レース結果のスクレイピング完了 ===")
        print("スクレイピング結果 先頭50:")
        print(tabulate(df.head(50), df.columns, tablefmt="presto", showindex=True))
        print("スクレイピング結果 末尾50:")
        print(tabulate(df.tail(50), df.columns, tablefmt="presto", showindex=True))

        print(f"Total records: {len(df)}")
