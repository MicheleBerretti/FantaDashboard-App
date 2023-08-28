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
    # Asking role
    role = st.radio("Which role you want to check?", ("All", "POR", "DIF", "CEN","TRQ", "ATT"))

    # Importing the dataset of the given role
    if role == "All":
        df = pd.read_csv('players.csv')
    else:
        df = pd.read_csv(f'db_{role}.csv')

    st.write("### Showing players for selected role:")
    st.write(df)


    if role != "All":

        df = df.sort_values("Punteggio", ascending=False)

        over = np.array(df["Punteggio"]).astype(float)
        playrs = np.array(df["Nome"]).astype(str)
        team = np.array(df["Squadra"]).astype(str)
        conf = np.array(df["Livello di confidenza"]).astype(float)

        conf_v = []
        for j in range(len(conf)):
            if conf[j] == 1:
                conf_v.append("High")
            elif conf[j] == 0.75:
                conf_v.append("Low")
            else:
                conf_v.append("Lowest")

        players_df = pd.DataFrame()

        players_df["Players"] = playrs[:20]
        players_df["Squadra"] = team[:20]
        players_df["Overall"] = over[:20]
        players_df["Livello di confidenza"] = conf[:20]

        st.write("### Quick look at top players in selected role:")
        st.write(players_df)

        f, ax = plt.subplots(figsize=(10, 5))
        sns.set_color_codes("pastel")


        sns.barplot(x=over[:20], y=playrs[:20], hue_order=conf_v[:20], label="Punteggio")

        # Add a legend and informative axis label
        plt.title(f"Top 20 {role}", fontsize=15)
        ax.legend(ncol=1, loc="best", frameon=False)
        ax.set(ylabel="",
            xlabel="Punteggio")
        sns.despine(left=True, bottom=True)
        st.pyplot(f)

 
 
with tab2:
    #Static, aggiornato di stagione in stagione per tenere conto di promossi e retrocessi
    team_name = ["Lazio", "Sassuolo", "Milan", "Cagliari", "Napoli", "Udinese", "Genoa", "Juventus", "Roma", "Atalanta", "Bologna", "Fiorentina", "Torino", "Verona", "Inter", "Empoli", "Frosinone", "Salernitana", "Lecce", "Monza"]
    team_id = [487, 488, 489, 490, 492, 494, 495, 496, 497, 499, 500, 502, 503, 504, 505, 511, 512, 514, 867, 1579]
    dict_team = dict(zip(team_name, team_id))

    conn = http.client.HTTPSConnection("v3.football.api-sports.io")

    headers = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': "848ca4816ddc2f145caa0e03175a7df8"
        }
    
    
    players_db = df = pd.read_csv('players.csv')

    player_name = st.selectbox("Which player you want to check?", players_db["Nome"])

    player_stats = players_db.loc[players_db['Nome'] == player_name]
    team_name = player_stats["Squadra"].values[0]
    if team_name == "Roma":
        st.toast("Daje Roma Daje", icon="🐺")
    player_role = player_stats["Ruolo"].values[0]
    st.write("### Showing stats for selected player:")
    st.write(player_stats) 
    
    
    # Make it recursive for each player in the team.

    team_score_list = []


    debug = False


    # Elenco giocatori in rosa

    #players_list = ["Pellegrini Lorenzo", "Osimhen Victor", "Dybala Paulo", "Mancini Gianluca", "Berardi Domenico", "Sanabria Antonio"]

    players_list = list(st.multiselect("Which players are in your team?", players_db["Nome"]))

    players_list_online = []

    for player_name in players_list:
        
        try:
        
            players_db = pd.read_csv("players.csv")
            player_stats = players_db.loc[players_db['Nome'] == player_name]
            team_name = player_stats["Squadra"].values[0]
            player_role = player_stats["Ruolo"].values[0]


            parsed = query_team(dict_team, team_name)
            

            index = []
            j=0
            for j in range(len(parsed["response"])):
                league = parsed["response"][j]["league"]["name"]
                if league == "Serie A":
                    index.append(j)


            latest_index = index[-1]
            latest_match_id = parsed["response"][latest_index]["fixture"]["id"]


            conn.request("GET", f"/predictions?fixture={latest_match_id}", headers=headers)

            res = conn.getresponse()
            data = res.read()
            parsed = json.loads(data)



            if parsed['response'][0]["teams"]["home"]["name"].find(team_name) != -1:
                home = 1
            else:
                home = 0
                
            if parsed['response'][0]["predictions"]["winner"]["name"].find(team_name) != -1:
                win = 1
            else:
                win = 0
                
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
                team_score = team_score + 3
                
            team_score += score_percentile(form)

            if check_role(player_role) == 1:
                team_score += score_percentile(form_att)
            else:
                team_score += score_percentile(form_def)
                
            team_score += score_percentile(poiss)

            team_score += score_percentile(total)

            team_score_list.append(team_score)
            players_list_online.append(player_name)
            
        except:
            st.toast("Error in fetching data for selected player", icon="⚠️")
        
    st.write("### Showing score for selected team:")
    st.write(dict(zip(players_list,team_score_list)))


    teams_df = pd.DataFrame()

    teams_df["Giocatori"] = players_list_online
    teams_df["Punteggio Squadra"] = team_score_list

    teams_df.sort_values(by="Punteggio Squadra", ascending=False, inplace=True)
    teams_df.reset_index(drop=True, inplace=True)
    if len(teams_df!=0):
        fig, ax = plt.subplots(figsize=(10, 5))

        sns.barplot(data=teams_df, x="Punteggio Squadra", y="Giocatori", color="r")

        # Add a legend and informative axis label
        plt.title(f"Classifica punteggio squadra rosa", fontsize=15)
        ax.legend(ncol=1, loc="best", frameon=False)
        ax.set(ylabel="",
            xlabel="Punteggio")
        sns.despine(left=True, bottom=True)
        st.pyplot(fig)
        
        
        
        
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
    avg1 = np.array(db_raw["Fantamedia anno 2020-2021"])
    avg2 = np.array(db_raw["Fantamedia anno 2021-2022"])
    avg3 = np.array(db_raw["Fantamedia anno 2022-2023"])
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


password = "Forza Roma!"

with tab3:
    
    password = st.text_input("", placeholder="Enter password", type="password", key="password")

    
    if password != st.secrets["UPDATER_PW"]:
        st.empty()
        st.write("## :red[You need to be an admin in order to access this section!]")
    
    
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            
            st.write("## :red[random debug stuff... Needs to be hidden better!]")
        
            players_urls = []
            for i in range(0, len(roles), 1):
                    list = get_players(roles[i])
                    [players_urls.append(k) for k in list]
            with open(r"players_urls.txt", "w") as fp:
                    for item in players_urls:
                        fp.write("%s\n" % item)            

        with col2:
            
            st.header("Database updater")
            if st.button("Update players database"):
                players_updater = []
                my_bar = st.progress(0, text="Downloading Database")
                steps_perc = 100/len(players_urls)
                for i in range(0, len(players_urls), 1):
                    player_up = get_attributes(players_urls[i])
                    players_updater.append(player_up)
                    my_bar.progress(int((i+1)*steps_perc), text="Downloading players database, please wait...")
                df = pd.DataFrame.from_dict(players_updater)
                df.to_csv("players.csv", index=False)
                st.toast("Players database updated", icon="✅")
                
            st.header("Export per role players database csv")
            try:
                database = pd.read_csv("players.csv")
            except:
                st.toast("Please update players database", icon="⚠️")
            if st.button("Goalkeeper"):
                csv_exporter(database, "POR")
                st.toast("Goalkeepers csv exported", icon="✅")
            if st.button("Defenders"):
                csv_exporter(database, "DIF")
                st.toast("Defenders csv exported", icon="✅")
            if st.button("Midfielders"):
                csv_exporter(database, "CEN")
                st.toast("Midfielders csv exported", icon="✅")
            if st.button("Attacking Midfielders"):
                csv_exporter(database, "TRQ")
                st.toast("Attacking Midfielders csv exported", icon="✅")
            if st.button("Forwards"):
                csv_exporter(database, "ATT")
                st.toast("Forwards csv exported", icon="✅")
            if st.button("All players"):
                csv_exporter(database, "POR")
                csv_exporter(database, "DIF")
                csv_exporter(database, "CEN")
                csv_exporter(database, "TRQ")
                csv_exporter(database, "ATT")
                st.toast("All players csv exported", icon="✅")
