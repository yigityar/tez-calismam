from google_play_scraper import search, app, reviews, Sort
import pandas as pd
import time

OUTPUT_FILE = "google_play_military_scores.csv"

# Anahtar kelimeler
KEYWORDS_NAME = [
    'MGRS','UTM','KOORDINAT','OFFLINE MAP','WAYPOINT','Ballistics',
    'Sniper Calculator','Bullet Drop','MOA','Mil-Dot','Rangefinder',
    'Dope Card','Milyem','Deployment Countdown','Shift Roster',
    'Push to Talk','Offline Mesh','tactical','army fitness',
    'military fitness','OPSEC','FYDT','Askeri','?afak Sayar','Nöbet'
]

KEYWORDS_DESC = [
    'askeri personel','operasyon','devriye','armed forces','platoon',
    'squad','deployment','combat','military operation','mission',
    'tactical','battlefield','No service area','Combat zone',
    'fiziki yeterlilik','kondisyon testi','intikal','Gozetleme',
    'PT test','military fitness','physical training','ACFT','PFT',
    'OPSEC','ISR','survaillance','reconnaissance','TSK','Jandarma',
    'Hudut','K??la','Komando'
]

KEYWORDS_REVIEW = [
    'birlik','tatbikat','platoon','squad','deployment','in the field',
    'military operation','mission','tactical','battlefield','Barracks',
    'patrol Base','No service area','Combat zone','fiziki yeterlilik',
    'kondisyon testi','army fitness','PT test','military fitness',
    'physical training','ACFT','PFT','OPSEC','ISR','reconnaissance',
    'FYDT','?afak','nöbet','komutan','devrem','tertip','üste?men',
    'ba?çavu?','astsubay','uzman çavu?','silah','mühimmat'
]

def calculate_score(text, keywords):
    if not text: return 0, ""
    text_lower = text.lower()
    matches = [kw for kw in keywords if kw.lower() in text_lower]
    count = sum(text_lower.count(kw.lower()) for kw in keywords)
    return count, ", ".join(set(matches))

results = []
scanned_packages = set()

print("--- GOOGLE PLAY ASKER? ANAL?Z BA?LIYOR ---")

for query in KEYWORDS_NAME:
    print(f"\n>>> Google Play'de Aran?yor: '{query}'")
    try:
        search_results = search(query, lang='tr', country='tr', n_hits=20)
        for app_item in search_results:
            pkg = app_item['appId']
            title = app_item['title']
            if pkg in scanned_packages:
                continue
            scanned_packages.add(pkg)

            print(f"   ?nceleniyor: {title[:25]}... ", end="")
            try:
                app_details = app(pkg, lang='tr', country='tr')
                desc_text = app_details['description']
                score_desc, match_desc = calculate_score(desc_text, KEYWORDS_DESC)
                score_name, match_name = calculate_score(title, KEYWORDS_NAME)

                # Türkçe yorumlar
                tr_reviews, _ = reviews(pkg, lang='tr', country='tr', sort=Sort.NEWEST, count=50)
                tr_text = " ".join([r['content'] for r in tr_reviews])
                score_rev_tr, match_rev_tr = calculate_score(tr_text, KEYWORDS_REVIEW)

                # ?ngilizce yorumlar
                en_reviews, _ = reviews(pkg, lang='en', country='us', sort=Sort.NEWEST, count=50)
                en_text = " ".join([r['content'] for r in en_reviews])
                score_rev_en, match_rev_en = calculate_score(en_text, KEYWORDS_REVIEW)

                # Toplam skor
                total_score = (score_name * 3) + (score_desc * 1) + ((score_rev_tr + score_rev_en) * 5)

                print(f"-> Puan: {total_score} (TR: {match_rev_tr}, EN: {match_rev_en})")

                if total_score > 0:
                    results.append({
                        "App Name": title,
                        "Package Name": pkg,
                        "Total Score": total_score,
                        "Review Matches TR": match_rev_tr,
                        "Review Matches EN": match_rev_en,
                        "Desc Matches": match_desc,
                        "Installs": app_details.get('minInstalls', 0),
                        "Score": app_details.get('score', 0),
                        "URL": app_details['url']
                    })

                time.sleep(1)

            except Exception as e:
                print(f"Hata: {e}")

    except Exception as e:
        print(f"Arama Hatas?: {e}")

if results:
    df = pd.DataFrame(results)
    df = df.sort_values(by="Total Score", ascending=False)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nANAL?Z B?TT?! Dosya: {OUTPUT_FILE}")
    print(df[['App Name','Total Score','Review Matches TR','Review Matches EN']].head(10))
else:
    print("Sonuç bulunamad?.")
