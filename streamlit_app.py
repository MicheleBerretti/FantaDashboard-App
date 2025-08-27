import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import http.client
import requests
from bs4 import BeautifulSoup
import time
from random import randint
import ast


# Create a function that given an array comprised between its max and its min, morphs it into a given range defined by a new min and a new max
def normalise(array, new_min, new_max):
    old_min = min(array)
    old_max = max(array)
    old_range = old_max - old_min
    new_range = new_max - new_min
    new_array = []
    for i in array:
        new_array.append(((i - old_min) / old_range) * new_range + new_min)
    return new_array

@st.cache_data()
def query_team(dict_team, team_name):
    conn.request("GET", f"/fixtures?team={dict_team[f'{team_name}']}&season=2022", headers=headers)
    res = conn.getresponse()
    data = res.read()
    data = data.decode("utf-8")
    parsed = json.loads(data)
    return parsed


@st.cache_data()
def score_percentile(x):
    if (x >= 0) and (x < 25):
        return 0
    elif (x >= 25) and (x < 50):
        return 1
    elif (x >= 50) and (x < 65):
        return 2.5
    elif (x >= 65) and (x < 75):
        return 3.5
    elif (x >= 75) and (x < 90):
        return 4.5
    elif (x >= 90) and (x <= 100):
        return 8
    else:
        return 0


@st.cache_data()
def check_role(x):
    if x == "CEN" or x == "ATT":
        return 1
    else:
        return 0
    


# Title
st.title(":orange[FantaCalcio Dashboard]")

tab1, tab2, tab3 = st.tabs(["Players Stats and Analysis", "Team Stats and Analysis", "Database Updater"])

with tab1:
    st.header("🔎 Player Stats and Analysis")
    st.markdown("Select a role to view player statistics, rankings, and confidence levels.")

    # Role selection with icons
    role_options = {
        "All": "All Roles",
        "POR": "🧤 Goalkeepers",
        "DIF": "🛡️ Defenders",
        "CEN": "⚙️ Midfielders",
        "TRQ": "🎩 Attacking Midfielders",
        "ATT": "🎯 Forwards"
    }
    role = st.radio("Choose role:", list(role_options.keys()), format_func=lambda x: role_options[x])

    # Load dataset
    if role == "All":
        df = pd.read_csv('players.csv')
    else:
        df = pd.read_csv(f'db_{role}.csv')

    st.subheader("Players Table")
    st.dataframe(df, use_container_width=True)

    if role != "All":
        df = df.sort_values("Punteggio", ascending=False)

        # Prepare top 20 players
        top_n = 20
        players_df = df.head(top_n)[["Nome", "Squadra", "Punteggio", "Livello di confidenza"]].copy()
        players_df.rename(columns={
            "Nome": "Player",
            "Squadra": "Team",
            "Punteggio": "Score",
            "Livello di confidenza": "Confidence"
        }, inplace=True)

        # Confidence as badge
        def confidence_badge(val):
            if val == 1:
                return "🟢 High"
            elif val == 0.75:
                return "🟡 Medium"
            else:
                return "🔴 Low"
        players_df["Confidence"] = players_df["Confidence"].apply(confidence_badge)

        st.markdown(f"#### 🏆 Top {top_n} {role_options[role]}")
        st.dataframe(players_df, use_container_width=True, height=500)

        # Bar chart
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=players_df, x="Score", y="Player", palette="viridis")
        plt.title(f"Top {top_n} {role_options[role]}", fontsize=16)
        ax.set_xlabel("Score")
        ax.set_ylabel("")
        st.pyplot(fig, use_container_width=True)

        # Show team distribution
        st.markdown("#### Team Distribution")
        team_counts = players_df["Team"].value_counts()
        st.bar_chart(team_counts)

 
 
with tab2:
    st.header("🏟️ Team Stats and Analysis")
    st.markdown("Analyze your fantasy team by selecting players and viewing their predicted scores based on upcoming fixtures.")

    # Static team info
    team_name = [
        "Lazio", "Sassuolo", "Milan", "Cagliari", "Napoli", "Udinese", "Genoa", "Juventus", "Roma", "Atalanta",
        "Bologna", "Fiorentina", "Torino", "Verona", "Inter", "Parma", "Pisa", "Cremonese", "Lecce", "Como"
    ]
    team_id = [487, 488, 489, 490, 492, 494, 495, 496, 497, 499, 500, 502, 503, 504, 505, 523, 801, 520, 867, 895]
    dict_team = dict(zip(team_name, team_id))

    conn = http.client.HTTPSConnection("v3.football.api-sports.io")
    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': "848ca4816ddc2f145caa0e03175a7df8"
    }

    players_db = pd.read_csv('players.csv')

    st.subheader("🔍 Individual Player Stats")
    player_name = st.selectbox("Select a player to view stats:", players_db["Nome"])
    player_stats = players_db.loc[players_db['Nome'] == player_name]
    team_name_selected = player_stats["Squadra"].values[0]
    if team_name_selected == "Roma":
        st.toast("Daje Roma Daje", icon="🐺")
    if team_name_selected == "Lazio":
        st.toast("Lazio Merda", icon="💩")
    player_role = player_stats["Ruolo"].values[0]

    with st.expander("Show selected player stats"):
        st.dataframe(player_stats, use_container_width=True)

    st.divider()

    st.subheader("👥 Team Score Prediction")
    st.markdown("Select your squad to see their predicted team scores for the next match.")

    players_list = st.multiselect(
        "Select players in your fantasy team:",
        players_db["Nome"],
        help="Choose multiple players to analyze your team."
    )

    team_score_list = []
    players_list_online = []

    progress = st.progress(0, text="Fetching team predictions...") if players_list else None

    for idx, player_name in enumerate(players_list):
        try:
            player_stats = players_db.loc[players_db['Nome'] == player_name]
            team_name = player_stats["Squadra"].values[0]
            player_role = player_stats["Ruolo"].values[0]

            parsed = query_team(dict_team, team_name)
            index = [j for j in range(len(parsed["response"])) if parsed["response"][j]["league"]["name"] == "Serie A"]
            latest_index = index[-1]
            latest_match_id = parsed["response"][latest_index]["fixture"]["id"]

            conn.request("GET", f"/predictions?fixture={latest_match_id}", headers=headers)
            res = conn.getresponse()
            data = res.read()
            parsed = json.loads(data)

            home = 1 if parsed['response'][0]["teams"]["home"]["name"].find(team_name) != -1 else 0
            win = 1 if parsed['response'][0]["predictions"]["winner"]["name"].find(team_name) != -1 else 0

            if home == 1:
                form = int(parsed['response'][0]["comparison"]["form"]["home"][0:2])
                form_att = int(parsed['response'][0]["comparison"]["att"]["home"][0:2])
                form_def = int(parsed['response'][0]["comparison"]["def"]["home"][0:2])
                poiss = int(parsed['response'][0]["comparison"]["poisson_distribution"]["home"][0:2])
                total = int(parsed['response'][0]["comparison"]["total"]["home"][0:2])
            else:
                form = int(parsed['response'][0]["comparison"]["form"]["away"][0:2])
                form_att = int(parsed['response'][0]["comparison"]["att"]["away"][0:2])
                form_def = int(parsed['response'][0]["comparison"]["def"]["away"][0:2])
                poiss = int(parsed['response'][0]["comparison"]["poisson_distribution"]["away"][0:2])
                total = int(parsed['response'][0]["comparison"]["total"]["away"][0:2])

            team_score = 0
            if win == 1:
                team_score += 3
            team_score += score_percentile(form)
            team_score += score_percentile(form_att if check_role(player_role) == 1 else form_def)
            team_score += score_percentile(poiss)
            team_score += score_percentile(total)

            team_score_list.append(team_score)
            players_list_online.append(player_name)
        except Exception as e:
            st.toast(f"Error fetching data for {player_name}", icon="⚠️")
        if progress:
            progress.progress((idx + 1) / len(players_list), text="Fetching team predictions...")

    if progress:
        progress.empty()

    if players_list_online:
        st.markdown("### 🏅 Team Score Table")
        teams_df = pd.DataFrame({
            "Player": players_list_online,
            "Team Score": team_score_list
        }).sort_values(by="Team Score", ascending=False).reset_index(drop=True)

        st.dataframe(teams_df, use_container_width=True, height=400)

        st.markdown("### 📊 Team Score Bar Chart")
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=teams_df, x="Team Score", y="Player", palette="rocket")
        plt.title("Team Score Ranking", fontsize=15)
        ax.set_xlabel("Score")
        ax.set_ylabel("")
        sns.despine(left=True, bottom=True)
        st.pyplot(fig, use_container_width=True)
    else:
        st.info("Select players to view your team score analysis.")
        
        
        
#################################################################################################
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#
#################################################################################################



roles= ["Portieri", "Difensori", "Centrocampisti", "Trequartisti", "Attaccanti"]

skills = {
    "Fuoriclasse": 1,
    "Titolare": 3,
    "Buona Media": 2,
    "Goleador": 4,
    "Assistman": 2,
    "Piazzati": 2,
    "Rigorista": 5,
    "Giovane talento": 2,
    "Panchinaro": -4,
    "Falloso": -2,
    "Outsider": 2,
}

@st.cache_data()
def get_players(role: str) -> list:

    html = requests.get(
        "https://www.fantacalciopedia.com/lista-calciatori-serie-a/"
        + role.lower()
        + "/"
    )
    soup = BeautifulSoup(html.content, "html.parser")
    players = []
    temp = soup.find_all("article")
    for value in temp:
        player = value.find("a").get("href")
        players.append(player)

    return players

@st.cache_data()
def get_attributes(url: str) -> dict:
    time.sleep(randint(0, 2000) / 1000)
    attributes = dict()
    html = requests.get(url.strip())
    soup = BeautifulSoup(html.content, "html.parser")
    attributes["Nome"] = soup.select_one("h1").get_text().strip()

    selector = "div.col_one_fourth:nth-of-type(1) span.stickdan"
    attributes["Punteggio"] = soup.select_one(selector).text.strip().replace("/100", "")

    selector = "	div.col_one_fourth:nth-of-type(n+2) div"
    avg = [k.find("span").text.strip() for k in soup.select(selector)]
    yrs = [
        k.find("strong").text.split(" ")[-1].strip() for k in soup.select(selector)
    ]
    i = 0
    for yr in yrs:
        attributes[f"Fantamedia anno {yr}"] = avg[i]
        i += 1

    selector = "div.col_one_third:nth-of-type(2) div"
    stats_last_yr = soup.select_one(selector)
    params = [
        el.text.strip().replace(":", "") for el in stats_last_yr.find_all("strong")
    ]
    values = [k.text.strip() for k in stats_last_yr.find_all("span")]
    attributes.update(dict(zip(params, values)))

    selector = ".col_one_third.col_last div"
    stats_prev = soup.select_one(selector)
    params = [
        k.text.strip().replace(":", "") for k in stats_prev.find_all("strong")
    ]
    values = [k.text.strip() for k in stats_prev.find_all("span")]
    attributes.update(dict(zip(params, values)))

    selector = ".label12 span.label"
    role = soup.select_one(selector)
    attributes["Ruolo"] = role.get_text().strip()

    selector = "span.stickdanpic"
    skills = [k.text for k in soup.select(selector)]
    attributes["Skills"] = skills

    selector = "div.progress-percent"
    inv = soup.select(selector)[2]
    attributes["Buon investimento"] = inv.text.replace("%", "")

    selector = "div.progress-percent"
    inv = soup.select(selector)[3]
    attributes["Resistenza infortuni"] = inv.text.replace("%", "")

    selector = "img.inf_calc"
    try:
        advised = soup.select_one(selector).get("title")
        if "Consigliato per la giornata" in advised:
            attributes["Consigliato prossima giornata"] = True
        else:
            attributes["Consigliato prossima giornata"] = False

    except:
        attributes["Consigliato prossima giornata"] = False

    selector = "span.new_calc"
    new = soup.select_one(selector)
    if not new == None:
        attributes["Nuovo acquisto"] = True
    else:
        attributes["Nuovo acquisto"] = False

    selector = "img.inf_calc"
    try:
        injured = soup.select_one(selector).get("title")
        if "Infortunato" in injured:
            attributes["Infortunato"] = True
        else:
            attributes["Infortunato"] = False

    except:
        attributes["Infortunato"] = False

    selector = "#content > div > div.section.nobg.nomargin > div > div > div:nth-child(2) > div.col_three_fifth > div.promo.promo-border.promo-light.row > div:nth-child(3) > div:nth-child(1) > div > img"
    team = soup.select_one(selector).get("title").split(":")[1].strip()
    attributes["Squadra"] = team

    selector = "	div.col_one_fourth:nth-of-type(n+2) div"
    try:
        trend = soup.select(selector)[0].find("i").get("class")[1]
        if trend == "icon-arrow-up":
            attributes["Trend"] = "UP"
        else:
            attributes["Trend"] = "DOWN"
    except:
        attributes["Trend"] = "STABLE"

    selector = "div.col_one_fourth:nth-of-type(2) span.rouge"
    played = soup.select_one(selector).text
    attributes["Presenze campionato corrente"] = played

    return attributes


@st.cache_data()
def csv_exporter(database, role):
    # Roles: POR, DIF, CEN, ATT
    # Housekeeping
    db_raw = database[database['Ruolo'] == role]

    warning_flag = []
    fatal_flag = []

    # Mise en place (*Proceeds to chefkiss*)

    team = np.array(db_raw["Squadra"])
    # Dynamically get the last three years for "Fantamedia anno XXXX-YYYY"
    current_year = pd.Timestamp.now().year
    avg1_col = f"Fantamedia anno {current_year-4}-{current_year-3}"
    avg2_col = f"Fantamedia anno {current_year-3}-{current_year-2}"
    avg3_col = f"Fantamedia anno {current_year-2}-{current_year-1}"

    avg1 = np.array(db_raw.get(avg1_col, ["nd"] * len(db_raw)))
    avg2 = np.array(db_raw.get(avg2_col, ["nd"] * len(db_raw)))
    avg3 = np.array(db_raw.get(avg3_col, ["nd"] * len(db_raw)))
    flag_new = np.array(db_raw['Nuovo acquisto']) # This needs to be better considered. Right now is just -3 malus for new players. 
    score_base = np.array(db_raw["Punteggio"]).astype(int)


    delta = []
    for j in range(len(avg3)):
        if avg3[j] != "nd" and avg2[j] != "nd" and avg1[j] != "nd":
            delta.append(round((float(avg3[j]) - float(avg1[j])), 1))
            warning_flag.append(False)
            fatal_flag.append(False)
        elif avg3[j] != "nd" and avg2[j] != "nd" and avg1[j] == "nd":
            delta.append(round((float(avg3[j]) - float(avg2[j])), 1))
            warning_flag.append(True)
            fatal_flag.append(False)
        else:
            delta.append(0)
            warning_flag.append(True)
            fatal_flag.append(True)

    # FINAL DATA PRODUCT 1: delta
    delta = np.array(delta)
    # AUX DATA PRODUCTS: warning_flag, fatal_flag


    pres = np.array(db_raw["Presenze previste"])
    gol = np.array(db_raw["Gol previsti"])
    assist = np.array(db_raw["Assist previsti"])    

    for i in range(len(gol)):
        pres[i] = pres[i][:2].replace("/", "").replace(" ", "")
        gol[i] = gol[i][:2].replace("/", "").replace(" ", "")
        assist[i] = assist[i][:2].replace("/", "").replace(" ", "")

    gol = gol.astype(int)
    pres = pres.astype(int)
    assist = assist.astype(int)

    ratio = []
    for i in range(len(gol)):
        if pres[i] == 0:
            ratio.append(0)
        else:
            if role == "POR":
                ratio.append(round(pres[i]/gol[i], 2))
            elif role == "DIF" or role == "CEN":
                ratio.append(round((0.4*gol[i]+0.8*assist[i])/pres[i], 2))
            else:
                ratio.append(round((0.8*gol[i]+0.4*assist[i])/pres[i], 2))

    # FINAL DATA PRODUCT 2: ratio (gol(+assist)/pres, lower is better for a gk, otherwise higher is better)
    ratio = np.array(ratio)

    pres = np.array(pres)
    pres = pres/pres.max()

    # FINAL DATA PRODUCT 3: pres (presenze, higher is better, 1 is max)

    inv = np.array(db_raw["Buon investimento"]).astype(float)/100
    inj_res = np.array(db_raw["Resistenza infortuni"]).astype(float)/100

    # FINAL DATA PRODUCT 4: inv (buon investimento, higher is better, 1 is max)
    inv = np.array(inv)
    # FINAL DATA PRODUCT 5: inj_res (resistenza infortuni, higher is better, 1 is max)
    inj_res = np.array(inj_res)

    inj = np.array(db_raw["Infortunato"])

    # FINAL DATA PRODUCT 6: inj (infortunato, boolean, True if injured)
    inj = np.array(inj)

    trend = np.array(db_raw["Trend"])
    for j,val in enumerate(trend):
        if val =="UP":
            trend[j] = 1
        elif val == "DOWN":
            trend[j] = -1
        else:
            trend[j] = 0.5

    # FINAL DATA PRODUCT 7: trend (trend, higher is better, 1 is max)
    trend = np.array(trend)

    skilled = np.array(db_raw["Skills"])


    skill_value = []
    for j in range(len(skilled)):
        skilled[j] = ast.literal_eval(skilled[j])
        kk = 0
        for value in skilled[j]:
            if value == "Titolare":
                kk+=0.1
            elif value == "Fuoriclasse":
                kk+=0.35
            elif value == "Buona Media":
                kk+=0.2
            elif value == "Goleador":
                kk+=0.4
            elif value == "Assistman":
                kk+=0.4
            elif value == "Piazzati":
                kk+=0.1
            elif value == "Rigorista":
                kk+=0.1
            elif value == "Giovane Talento":
                kk+=0.05
            elif value == "Panchinaro":
                kk+=-0.4
            elif value == "Falloso":
                kk+=-0.3
            elif value == "Outsider":
                kk+=0.05
            else:
                pass
        skill_value.append(round(kk,2))

    confidence = []

    for j in range(len(warning_flag)):
        if warning_flag[j] == True and fatal_flag[j] == False:
            confidence.append(0.75)
        elif warning_flag[j] == True and fatal_flag[j] == True:
            confidence.append(0.5)
        else:
            confidence.append(1)

    # FINAL DATA PRODUCT 8: skill_value (skill_value, higher is better, 1 is max)
    skill_value = np.array(skill_value)


    # Scoring
    score = []

    delta_norm = normalise(delta, 0, 5)
    delta_norm = np.array(delta_norm)
    ratio_norm = normalise(ratio, 0, 7)
    ratio_norm = np.array(ratio_norm)
    pres_norm = normalise(pres, 0, 7)
    pres_norm = np.array(pres_norm)
    inv_norm = normalise(inv, 0, 5)
    inv_norm = np.array(inv_norm)
    inj_res_norm = normalise(inj_res, 0, 5)
    inj_res_norm = np.array(inj_res_norm)
    trend_norm = normalise(trend, 0, 2)
    trend_norm = np.array(trend_norm)
    skill_value_norm = normalise(skill_value, 0, 10)
    skill_value_norm = np.array(skill_value_norm)
    score_base_norm = normalise(score_base, 0, 50)
    score_base_norm = np.array(score_base_norm)

    flag_new_norm = []
    for j in range(len(flag_new)):
        if flag_new[j] == True:
            flag_new_norm = 0
        else:
            flag_new_norm = 5
    flag_new_norm = np.array(flag_new_norm)


    inj_norm = []
    for j in range(len(inj)):
        if inj[j] == True:
            inj_norm.append(0)
        else:
            inj_norm.append(4)
    inj_norm = np.array(inj_norm)

    # Sum all the normalised arrays
    score = delta_norm + ratio_norm + pres_norm + inv_norm + inj_res_norm + trend_norm + skill_value_norm + score_base_norm + flag_new_norm + inj_norm

    score = [round(i, 2) for i in score]

    # Goalkeepers clean database

    db = pd.DataFrame()
    db["Nome"] = db_raw["Nome"]
    db["Squadra"] = team
    db["Trend Stagionale"] = delta
    db["Ratio Gol/Pres"] = ratio
    db["Presenze"] = pres
    db["Buon Investimento"] = inv
    db["Resistenza Infortuni"] = inj_res
    db["Infortunato"] = inj
    db["Trend"] = trend
    db["Skill Value"] = skill_value
    db["Punteggio Base"] = score_base
    db["Nuovo Acquisto"] = flag_new
    db["Punteggio"] = score
    db["Livello di confidenza"] = confidence


    db.to_csv(f"db_{role}.csv", index=False)


password = "Forza Roma!" # This is just a placeholder, please use Streamlit secrets management to set a real password

with tab3:
    
    password = st.text_input("", placeholder="Enter password", type="password", key="password")

    
    if password != st.secrets["UPDATER_PW"]:
        st.empty()
        st.write("## :red[You need to be an admin in order to access this section!]")
    
    
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            st.header("Players URLs Debug")
            st.caption("This section is for admin/debug purposes. URLs are used for database updates.")

            players_urls = []
            for role in roles:
                urls = get_players(role)
                players_urls.extend(urls)

            # Show summary info instead of raw debug output
            st.write(f"Total player URLs fetched: **{len(players_urls)}**")
            st.write("Example URLs:", players_urls[:2])

            # Save URLs to file
            with open("players_urls.txt", "w") as fp:
                for item in players_urls:
                    fp.write("%s\n" % item)

            st.success("Players URLs have been saved to players_urls.txt")

        with col2:
            st.header("Database updater")

            if st.button("🔄 Update players database"):
                players_updater = []
                my_bar = st.progress(0)
                steps_perc = 100 / len(players_urls)

                with st.spinner("Downloading players database..."):
                    start_time = time.time()
                    for i, url in enumerate(players_urls):
                        player_up = get_attributes(url)
                        players_updater.append(player_up)
                        my_bar.progress(int((i + 1) * steps_perc))
                        # ETA calculation (overwrite previous line)
                        elapsed = time.time() - start_time
                        avg_time = elapsed / (i + 1)
                        remaining = avg_time * (len(players_urls) - (i + 1))
                        eta_str = time.strftime('%M:%S', time.gmtime(remaining))
                        # st.caption(f"ETA: {eta_str} remaining", unsafe_allow_html=True)

                df = pd.DataFrame(players_updater)
                df.to_csv("players.csv", index=False)
                st.toast("Players database updated", icon="✅")

            st.header("Export players database by role")

            try:
                database = pd.read_csv("players.csv")
            except FileNotFoundError:
                st.warning("⚠️ Please update players database first.")
                database = None

            if database is not None:
                roles = {
                    "Goalkeepers": "POR",
                    "Defenders": "DIF",
                    "Midfielders": "CEN",
                    "Attacking Midfielders": "TRQ",
                    "Forwards": "ATT",
                }

                # Display buttons in two columns for a cleaner layout
                col_a, col_b = st.columns(2)
                for i, (role_name, role_code) in enumerate(roles.items()):
                    col = col_a if i % 2 == 0 else col_b
                    if col.button(role_name):
                        csv_exporter(database, role_code)
                        st.toast(f"{role_name} csv exported", icon="✅")

                # Special "all players" button below
                if st.button("📦 Export All Players"):
                    for role_code in roles.values():
                        csv_exporter(database, role_code)
                    st.toast("All players csv exported", icon="✅")