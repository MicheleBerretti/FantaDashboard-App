import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import http.client

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

tab1, tab2 = st.tabs(["Players Stats and Analysis", "Team Stats and Analysis"])

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
