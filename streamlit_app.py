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
    role = st.radio("Which role you want to check?", ("All", "Goalkeeper", "Defender", "Midfielder", "Attacker"))

    # Importing the dataset of the given role
    if role == "Goalkeeper":
        df = pd.read_csv('portieri.csv')
    elif role == "Defender":
        df = pd.read_csv('difensori.csv')
    elif role == "Midfielder":
        df = pd.read_csv('centrocampisti.csv')
    elif role == "Attacker":
        df = pd.read_csv('attaccanti.csv')
    else:
        df = pd.read_csv('players.csv')

    st.write("### Showing players for selected role:")
    st.write(df)


    if role != "All":

        df = df.sort_values("Punteggio Goduria", ascending=False)

        over = np.array(df["Punteggio Goduria"]).astype(float)
        mult = np.array(df["Base Moltiplicativa"]).astype(float)
        add = np.array(df["Base Additiva"]).astype(float)
        live = np.array(df["Live Updates"]).astype(float)
        players = np.array(df["Giocatore"]).astype(str)
        team = np.array(df["Squadra"]).astype(str)

        players_df = pd.DataFrame()

        players_df["Players"] = players
        players_df["Squadra"] = team
        players_df["Base Moltiplicativa"] = mult
        players_df["Base Additiva"] = add
        players_df["Live Update"] = live
        players_df["Overall"] = over

        st.write("### Quick look at top players in selected role:")
        st.write(players_df)

        
        # Plotting the data
        
        players = np.array(players_df[:20]["Players"])
        overall = np.array(players_df[:20]["Overall"])
        mult = np.array(players_df[:20]["Base Moltiplicativa"])
        add = np.array(players_df[:20]["Base Additiva"])
        live = np.array(players_df[:20]["Live Update"])

        f, ax = plt.subplots(figsize=(10, 5))
        sns.set_color_codes("pastel")


        sns.barplot(data=players_df, x=overall, y=players, color="b", label="Overall")
        sns.barplot(data=players_df, x=mult, y=players, color="r", label="Base Moltiplicativa")
        sns.barplot(data=players_df, x=add, y=players, color="g", label="Base Additiva")
        sns.barplot(data=players_df, x=live, y=players, color="y", label="Live Update")

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




def gk_csv(database):
    gk = database[database["Ruolo"] == "POR"]
    team = np.array(gk["Squadra"])
    avg1 = np.array(gk["Fantamedia anno 2020-2021"])
    avg2 = np.array(gk["Fantamedia anno 2021-2022"])
    avg3 = np.array(gk["Fantamedia anno 2022-2023"])
    flag_new = np.array(gk['Nuovo acquisto'])
    score_base = np.array(gk["Punteggio"]).astype(int)

    for i in range(len(avg1)):
        if flag_new[i] == True:
            flag_new[i] = 0
        else:
            flag_new[i] = 1
        if avg3[i] == "nd":
            avg3[i] = 0
        if avg2[i] == "nd":
            avg2[i] = avg3[i]
        if avg1[i] == "nd":
            avg1[i] = avg2[i]

    flag_new = flag_new.astype(int)
    avg1 = avg1.astype(float)
    avg2 = avg2.astype(float)
    avg3 = avg3.astype(float)
    delta1 = avg2 - avg1
    delta2 = avg3 - avg1
    delta = ((delta1 + delta2)*flag_new)
    gk["Delta Fantamedia"] = delta

    delta = delta/100



    pres = np.array(gk["Presenze previste"])
    gol = np.array(gk["Gol previsti"])
    ass = np.array(gk["Assist previsti"])

    for i in range(len(gol)):
        pres[i] = pres[i][:2].replace("/", "").replace(" ", "")
        gol[i] = gol[i][:2].replace("/", "").replace(" ", "")
        ass[i] = ass[i][:2].replace("/", "").replace(" ", "")

    gol = gol.astype(float)
    pres = pres.astype(float)
    ass = ass.astype(float)

    null = []

    for i in range(len(gol)):
        if pres[i] == 0:
            null.append(0)
        else:
            null.append(1)

    kda = (gol+ass)/pres
    null = np.array(null)
    kda = kda*null
    kda = np.nan_to_num(kda, nan=0.0)

    pres = pres/(pres.max())

    score1 = (kda/10) + (pres/10)

    score0 = score_base*(0.3+delta+score1)

    gok = pd.DataFrame()
    gok["Giocatore"] = np.array(gk["Nome"])
    gok["Miglioramento Stagionale"] = delta
    gok["Gol/Presenze"] = score1
    gok["Base Moltiplicativa"] = score0

    skilled = np.array(gk["Skills"])
    new = np.array(gk["Nuovo acquisto"]).astype(bool)
    inv = np.array(gk["Buon investimento"]).astype(float)
    inj_res = np.array(gk["Resistenza infortuni"]).astype(float)


    skill_value = []
    for j in range(len(skilled)):
        skilled[j] = ast.literal_eval(skilled[j])
        kk = 0
        if new[j] == True:
            kk = -3
        kk+=inv[j]/20
        kk+=inj_res[j]/20
        for value in skilled[j]:
            if value == "Titolare":
                kk+=3
            elif value == "Fuoriclasse":
                kk+=1
            elif value == "Buona Media":
                kk+=2
            elif value == "Goleador":
                kk+=4
            elif value == "Assistman":
                kk+=2
            elif value == "Piazzati":
                kk+=2
            elif value == "Rigorista":
                kk+=5
            elif value == "Giovane Talento":
                kk+=2
            elif value == "Panchinaro":
                kk+=-4
            elif value == "Falloso":
                kk+=-2
            elif value == "Outsider":
                kk+=2
            else:
                pass

        skill_value.append(kk)

    score2 = np.array(skill_value)
    gok["Base Additiva"] = score2

    recom = np.array(gk["Consigliato prossima giornata"])
    inj = np.array(gk["Infortunato"])
    trend = np.array(gk["Trend"])


    score3 = []

    for j in range(len(recom)):
        kk = 0
        if recom[j] == True:
            kk+=5
        if inj[j] == True:
            kk-=10
        if trend[j] =="UP":
            kk+=8
        elif trend[j] =="STABLE":
            kk+=2
        elif trend[j] == "DOWN":
            kk-=5
        score3.append(kk)

    score3 = np.array(score3)

    gok["Live Updates"] = score3

    score0 = (60*score0)/score0.max()
    score2 = (20*score2)/score2.max()
    score3 = (20*score3)/score3.max()

    goduria_score = score0+score2+score3

    gok["Punteggio Goduria"] = goduria_score
    gok["Squadra"] = team
    gok = gok.sort_values("Punteggio Goduria", ascending=False)

    gok.to_csv("portieri.csv")



def dc_csv(database):
    dc = database[database["Ruolo"] == "DIF"]
    team = np.array(dc["Squadra"])

    avg1 = np.array(dc["Fantamedia anno 2020-2021"])
    avg2 = np.array(dc["Fantamedia anno 2021-2022"])
    avg3 = np.array(dc["Fantamedia anno 2022-2023"])
    flag_new = np.array(dc['Nuovo acquisto'])
    score_base = np.array(dc["Punteggio"]).astype(int)

    for i in range(len(avg1)):
        if flag_new[i] == True:
            flag_new[i] = 0
        else:
            flag_new[i] = 1
        if avg3[i] == "nd":
            avg3[i] = 0
        if avg2[i] == "nd":
            avg2[i] = avg3[i]
        if avg1[i] == "nd":
            avg1[i] = avg2[i]

    flag_new = flag_new.astype(int)
    avg1 = avg1.astype(float)
    avg2 = avg2.astype(float)
    avg3 = avg3.astype(float)
    delta1 = avg2 - avg1
    delta2 = avg3 - avg1
    delta = ((delta1 + delta2)*flag_new)

    delta = (delta/delta.max())/10


    dc["Delta Fantamedia"] = delta


    pres = np.array(dc["Presenze previste"])
    gol = np.array(dc["Gol previsti"])
    ass = np.array(dc["Assist previsti"])

    for i in range(len(gol)):
        pres[i] = pres[i][:2].replace("/", "").replace(" ", "")
        gol[i] = gol[i][:2].replace("/", "").replace(" ", "")
        ass[i] = ass[i][:2].replace("/", "").replace(" ", "")

    gol = gol.astype(float)
    pres = pres.astype(float)
    ass = ass.astype(float)

    null = []

    for i in range(len(gol)):
        if pres[i] == 0:
            null.append(0)
        else:
            null.append(1)

    kda = (gol+ass)/pres
    null = np.array(null)
    kda = kda*null
    kda = np.nan_to_num(kda, nan=0.0)

    pres = pres/(pres.max())

    score1 = (kda/10) + (pres/10)

    score0 = score_base*(0.3+delta+score1)

    dif = pd.DataFrame()
    dif["Giocatore"] = np.array(dc["Nome"])
    dif["Miglioramento Stagionale"] = delta
    dif["Gol/Presenze"] = score1
    dif["Base Moltiplicativa"] = score0


    skilled = np.array(dc["Skills"])
    new = np.array(dc["Nuovo acquisto"]).astype(bool)
    inv = np.array(dc["Buon investimento"]).astype(float)
    inj_res = np.array(dc["Resistenza infortuni"]).astype(float)

    skill_value = []
    for j in range(len(skilled)):
        skilled[j] = ast.literal_eval(skilled[j])
        kk = 0
        if new[j] == True:
            kk = -3
        kk+=inv[j]/20
        kk+=inj_res[j]/20
        for value in skilled[j]:
            if value == "Titolare":
                kk+=3
            elif value == "Fuoriclasse":
                kk+=1
            elif value == "Buona Media":
                kk+=2
            elif value == "Goleador":
                kk+=4
            elif value == "Assistman":
                kk+=2
            elif value == "Piazzati":
                kk+=2
            elif value == "Rigorista":
                kk+=5
            elif value == "Giovane Talento":
                kk+=2
            elif value == "Panchinaro":
                kk+=-4
            elif value == "Falloso":
                kk+=-2
            elif value == "Outsider":
                kk+=2
            else:
                pass

        skill_value.append(kk)

    score2 = np.array(skill_value)
    dif["Base Additiva"] = score2

    recom = np.array(dc["Consigliato prossima giornata"])
    inj = np.array(dc["Infortunato"])
    trend = np.array(dc["Trend"])


    score3 = []

    for j in range(len(recom)):
        kk = 0
        if recom[j] == True:
            kk+=5
        if inj[j] == True:
            kk-=10
        if trend[j] =="UP":
            kk+=8
        elif trend[j] =="STABLE":
            kk+=2
        elif trend[j] == "DOWN":
            kk-=5
        score3.append(kk)

    score3 = np.array(score3)

    dif["Live Updates"] = score3

    score0 = (60*score0)/score0.max()
    score2 = (20*score2)/score2.max()
    score3 = (20*score3)/score3.max()

    goduria_score = score0+score2+score3

    dif["Punteggio Goduria"] = goduria_score
    dif["Squadra"] = team
    dif = dif.sort_values("Punteggio Goduria", ascending=False)

    dif.to_csv("difensori.csv")


def cc_csv(database):
    cc = database[database["Ruolo"] == "CEN"]
    team = np.array(cc["Squadra"])

    avg1 = np.array(cc["Fantamedia anno 2020-2021"])
    avg2 = np.array(cc["Fantamedia anno 2021-2022"])
    avg3 = np.array(cc["Fantamedia anno 2022-2023"])
    flag_new = np.array(cc['Nuovo acquisto'])
    score_base = np.array(cc["Punteggio"]).astype(int)

    for i in range(len(avg1)):
        if flag_new[i] == True:
            flag_new[i] = 0
        else:
            flag_new[i] = 1
        if avg3[i] == "nd":
            avg3[i] = 0
        if avg2[i] == "nd":
            avg2[i] = avg3[i]
        if avg1[i] == "nd":
            avg1[i] = avg2[i]

    flag_new = flag_new.astype(int)
    avg1 = avg1.astype(float)
    avg2 = avg2.astype(float)
    avg3 = avg3.astype(float)
    delta1 = avg2 - avg1
    delta2 = avg3 - avg1
    delta = ((delta1 + delta2)*flag_new)

    delta = (delta/delta.max())/10


    cc["Delta Fantamedia"] = delta


    pres = np.array(cc["Presenze previste"])
    gol = np.array(cc["Gol previsti"])
    ass = np.array(cc["Assist previsti"])

    for i in range(len(gol)):
        pres[i] = pres[i][:2].replace("/", "").replace(" ", "")
        gol[i] = gol[i][:2].replace("/", "").replace(" ", "")
        ass[i] = ass[i][:2].replace("/", "").replace(" ", "")

    gol = gol.astype(float)
    pres = pres.astype(float)
    ass = ass.astype(float)

    null = []

    for i in range(len(gol)):
        if pres[i] == 0:
            null.append(0)
        else:
            null.append(1)

    kda = (gol+ass)/pres
    null = np.array(null)
    kda = kda*null
    kda = np.nan_to_num(kda, nan=0.0)

    pres = pres/(pres.max())

    score1 = (kda/10) + (pres/10)

    score0 = score_base*(0.3+delta+score1)

    cen = pd.DataFrame()
    cen["Giocatore"] = np.array(cc["Nome"])
    cen["Miglioramento Stagionale"] = delta
    cen["Gol/Presenze"] = score1
    cen["Base Moltiplicativa"] = score0

    skilled = np.array(cc["Skills"])
    new = np.array(cc["Nuovo acquisto"]).astype(bool)
    inv = np.array(cc["Buon investimento"]).astype(float)
    inj_res = np.array(cc["Resistenza infortuni"]).astype(float)

    skill_value = []
    for j in range(len(skilled)):
        skilled[j] = ast.literal_eval(skilled[j])
        kk = 0
        if new[j] == True:
            kk = -3
        kk+=inv[j]/20
        kk+=inj_res[j]/20
        for value in skilled[j]:
            if value == "Titolare":
                kk+=3
            elif value == "Fuoriclasse":
                kk+=1
            elif value == "Buona Media":
                kk+=2
            elif value == "Goleador":
                kk+=4
            elif value == "Assistman":
                kk+=2
            elif value == "Piazzati":
                kk+=2
            elif value == "Rigorista":
                kk+=5
            elif value == "Giovane Talento":
                kk+=2
            elif value == "Panchinaro":
                kk+=-4
            elif value == "Falloso":
                kk+=-2
            elif value == "Outsider":
                kk+=2
            else:
                pass

        skill_value.append(kk)

    score2 = np.array(skill_value)
    cen["Base Additiva"] = score2

    recom = np.array(cc["Consigliato prossima giornata"])
    inj = np.array(cc["Infortunato"])
    trend = np.array(cc["Trend"])


    score3 = []

    for j in range(len(recom)):
        kk = 0
        if recom[j] == True:
            kk+=5
        if inj[j] == True:
            kk-=10
        if trend[j] =="UP":
            kk+=8
        elif trend[j] =="STABLE":
            kk+=2
        elif trend[j] == "DOWN":
            kk-=5
        score3.append(kk)

    score3 = np.array(score3)

    cen["Live Updates"] = score3

    score0 = (60*score0)/score0.max()
    score2 = (20*score2)/score2.max()
    score3 = (20*score3)/score3.max()

    goduria_score = score0+score2+score3

    cen["Punteggio Goduria"] = goduria_score
    cen["Squadra"] = team
    cen = cen.sort_values("Punteggio Goduria", ascending=False)

    cen.to_csv("centrocampisti.csv")


def atk_csv(database):
    att = database[database["Ruolo"] == "ATT"]
    team = np.array(att["Squadra"])

    avg1 = np.array(att["Fantamedia anno 2020-2021"])
    avg2 = np.array(att["Fantamedia anno 2021-2022"])
    avg3 = np.array(att["Fantamedia anno 2022-2023"])
    flag_new = np.array(att['Nuovo acquisto'])
    score_base = np.array(att["Punteggio"]).astype(int)

    for i in range(len(avg1)):
        if flag_new[i] == True:
            flag_new[i] = 0
        else:
            flag_new[i] = 1
        if avg3[i] == "nd":
            avg3[i] = 0
        if avg2[i] == "nd":
            avg2[i] = avg3[i]
        if avg1[i] == "nd":
            avg1[i] = avg2[i]

    flag_new = flag_new.astype(int)
    avg1 = avg1.astype(float)
    avg2 = avg2.astype(float)
    avg3 = avg3.astype(float)
    delta1 = avg2 - avg1
    delta2 = avg3 - avg1
    delta = ((delta1 + delta2)*flag_new)

    delta = (delta/delta.max())/10


    att["Delta Fantamedia"] = delta


    pres = np.array(att["Presenze previste"])
    gol = np.array(att["Gol previsti"])
    ass = np.array(att["Assist previsti"])

    for i in range(len(gol)):
        pres[i] = pres[i][:2].replace("/", "").replace(" ", "")
        gol[i] = gol[i][:2].replace("/", "").replace(" ", "")
        ass[i] = ass[i][:2].replace("/", "").replace(" ", "")

    gol = gol.astype(float)
    pres = pres.astype(float)
    ass = ass.astype(float)

    null = []

    for i in range(len(gol)):
        if pres[i] == 0:
            null.append(0)
        else:
            null.append(1)

    kda = (gol+ass)/pres
    null = np.array(null)
    kda = kda*null
    kda = np.nan_to_num(kda, nan=0.0)

    pres = pres/(pres.max())

    score1 = (kda/10) + (pres/10)

    score0 = score_base*(0.3+delta+score1)

    atk = pd.DataFrame()
    atk["Giocatore"] = np.array(att["Nome"])
    atk["Miglioramento Stagionale"] = delta
    atk["Gol/Presenze"] = score1
    atk["Base Moltiplicativa"] = score0

    skilled = np.array(att["Skills"])
    new = np.array(att["Nuovo acquisto"]).astype(bool)
    inv = np.array(att["Buon investimento"]).astype(float)
    inj_res = np.array(att["Resistenza infortuni"]).astype(float)

    skill_value = []
    for j in range(len(skilled)):
        skilled[j] = ast.literal_eval(skilled[j])
        kk = 0
        if new[j] == True:
            kk = -3
        kk+=inv[j]/20
        kk+=inj_res[j]/20
        for value in skilled[j]:
            if value == "Titolare":
                kk+=3
            elif value == "Fuoriclasse":
                kk+=1
            elif value == "Buona Media":
                kk+=2
            elif value == "Goleador":
                kk+=4
            elif value == "Assistman":
                kk+=2
            elif value == "Piazzati":
                kk+=2
            elif value == "Rigorista":
                kk+=5
            elif value == "Giovane Talento":
                kk+=2
            elif value == "Panchinaro":
                kk+=-4
            elif value == "Falloso":
                kk+=-2
            elif value == "Outsider":
                kk+=2
            else:
                pass

        skill_value.append(kk)

    score2 = np.array(skill_value)
    atk["Base Additiva"] = score2

    recom = np.array(att["Consigliato prossima giornata"])
    inj = np.array(att["Infortunato"])
    trend = np.array(att["Trend"])


    score3 = []

    for j in range(len(recom)):
        kk = 0
        if recom[j] == True:
            kk+=5
        if inj[j] == True:
            kk-=10
        if trend[j] =="UP":
            kk+=8
        elif trend[j] =="STABLE":
            kk+=2
        elif trend[j] == "DOWN":
            kk-=5
        score3.append(kk)

    score3 = np.array(score3)

    atk["Live Updates"] = score3

    score0 = (60*score0)/score0.max()
    score2 = (20*score2)/score2.max()
    score3 = (20*score3)/score3.max()

    goduria_score = score0+score2+score3

    atk["Punteggio Goduria"] = goduria_score
    atk["Squadra"] = team
    atk = atk.sort_values("Punteggio Goduria", ascending=False)

    atk.to_csv("attaccanti.csv")



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
                gk_csv(database)
                st.toast("Goalkeepers csv exported", icon="✅")
            if st.button("Defenders"):
                dc_csv(database)
                st.toast("Defenders csv exported", icon="✅")
            if st.button("Midfielders"):
                cc_csv(database)
                st.toast("Midfielders csv exported", icon="✅")
            if st.button("Forwards"):
                atk_csv(database)
                st.toast("Forwards csv exported", icon="✅")
            if st.button("All players"):
                gk_csv(database)
                dc_csv(database)
                cc_csv(database)
                atk_csv(database)
                st.toast("All players csv exported", icon="✅")
