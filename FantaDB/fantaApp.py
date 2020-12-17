from flask import Flask, render_template,  request, redirect, url_for, flash

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Date, Integer, Text, create_engine, inspect, exc, join
from sqlalchemy.sql import select

from FantaDB.models import FantaAllenatore, Squadra, Giocatore, FantaSquadra
from FantaDB.database import db_session, init_db

# Lettura file xsl
from pandas import DataFrame, read_csv
import pandas as pd 
import xlrd
import csv
import random

import os

# --- Setting Flask  ------------------------------------------------------------------------------------------------------------------
IMAGES= os.path.join('static', 'images')
app = Flask(__name__)
app.config['SECRET_KEY'] = 'lucailpesce' # Settata per usare il messaggio flash

# Setup della cartella che contiene le immagini
app.config['IMAGES']= IMAGES
full_filename= os.path.join(app.config['IMAGES'],  'fantacalcioLogo.jpg')


#---- Routes  -------------------------------------------------------------------------------------------------------------------------


@app.route("/",  methods=['GET','POST'])
def home():
    # Spezzo la rappresentazione di FantaAllenatore per l'elaborazione
    usernames, emails, results= getFantaMisterDB()


    print("Mister presenti nel database: ", results)
    # POST suddiviso in due parti, la prima parte verifica se si arriva in post sulla home per cancellare dei fantallenatori, la seconda è per vedere se si arriva in post per aggiungere fantallenatori
    if request.method == 'POST':

        op= request.form['op']

        if op == 'delete':
            idForm=  request.form['Id']
            # print("idForm :", idForm)

            if len(idForm) > 0:
                # Se il fantaAllenatore che vogliamo eliminare ha una fantasquadra prima eliminiamo questa poi lui (si potrebbe aggiungere che una volta eliminato l'utente, tutte le info relative a lui (compreso i suoi giocatori) vengono cancellate)
                for mister in results:
                    if int(idForm) == int(mister[0]):
                        FantaSquadra.query.filter_by(IdFantaAllenatore= idForm).delete()
                        db_session.commit()
                
                FantaAllenatore.query.filter_by(id=idForm).delete()
                db_session.commit()
                return redirect('/')
        else:
            # Controllo il formato dell'email 
            print("username :", request.form['username'])
            if request.form['username'] != '': 
                if '@' in request.form['Email'] and ('.com'  in request.form['Email'] or '.it'  in request.form['Email']):
                    if request.form['Email'] not in emails and request.form['username'] not in usernames: 

                        IDmister= CreateID(FantaAllenatore)

                        if IDmister != 'F':
                            mister = FantaAllenatore(IDmister, request.form['Email'], request.form['username'])
                            db_session.add(mister)
                            db_session.commit()
                            return redirect('/')
                        else:
                            # flash("Numero d'iscrizioni massimo raggiunto!")
                            message= ["Numero d'iscrizioni massimo raggiunto!"]
                            render_template('homescreen.html', data=results, user_image= full_filename, messages= message)
                    else: 
                        # flash("Username o Email già utilizzati!")
                        message= ["Username o Email già utilizzati!"]
                        return render_template('homescreen.html', data=results, user_image= full_filename, messages= message)
                else:
                    # flash("Formato email sbagliato, ricontrollare!")
                    message= ["Formato email sbagliato, ricontrollare!"]
                    return render_template('homescreen.html', data=results, user_image= full_filename, messages= message)
                
            flash("Inserire Username!")
            return redirect('/')
    
    return render_template('homescreen.html', data=results, user_image= full_filename)

@app.route('/updateFAll', methods=['POST', 'GET'])
def updateFAll():
    nomeFantaTeam, idFantaAll, crediti, dictTeam= getFantaSquadre()

    # print("nomeFantaTeam: ", nomeFantaTeam)
    # print("\nidFantaAll: ", idFantaAll)

    op= request.form['op']
    # print("op: ", op)
    if request.method == 'POST':
        
        if op == "update":
            # Arrivo da homescreen con i dati del fantallenatore che voglio modificare                        
            iDForm= request.form['Id'] # questo Id qui è quello che viene dalla form di homescreen
            iD= int(iDForm) # Se non faccio cosi' iD = ' 9' con lo spazio

            nameAllenatore= request.form['name']
            email= request.form['email']

            if int(iD) in idFantaAll:
                # Se l'allenatore ha una fantasquadra non metto la possibilità d'inserirla e quindi posso solo vedere la squadra o cancellarla
                return render_template('updateFAll.html', op=op, id=iD, nAllenatore= nameAllenatore, email= email, fantaT= 'y', dictTeam= dictTeam, )

            # Se l'allenatore non ha una fantasquadra abilito la possibilità di aggiungerla 
            return render_template('updateFAll.html',op=op, id=iD, nAllenatore= nameAllenatore, email= email, fantaT= 'n')

        elif op == "addFTeam":
            # print("nTeam ricevuto: ", request.form['nTeam']) 
            # Creazione della FantaSquadra
            if request.form['nTeam'] not in nomeFantaTeam:
                iD= request.form['iD']
                fantaTeam= FantaSquadra(request.form['nTeam'], int(iD))

                db_session.add(fantaTeam)
                db_session.commit()
                return redirect('/')
            else:
                message= ["Nome Squadra gia presente!"]
                return render_template('updateFAll.html', messages= message)
        
        elif op == "deleteFTeam":
            FantaSquadra.query.filter_by(TeamName= request.form['nFTeam']).delete() # Volendo eventuale controllo su nFTeam dato che viene direttamente dalla form
            db_session.commit()
            return redirect('/')
        
        elif op == "updating":
            # Arrivo da updataFAll con i nuovi dati per effettuare la modifica
            iD= request.form['iD']
            nameAllenatore= request.form['username']
            emailAll= request.form['email']


            fAllenatore= FantaAllenatore.query.filter(FantaAllenatore.id == iD).one()
            fAllenatore.username= nameAllenatore
            fAllenatore.email= emailAll
            db_session.commit()
            # print("Utente modificato con successo")
            return redirect('/')

    elif request.method == 'GET':
        return render_template('homescreen.html', message=" Errore, pagina visitata in GET")
    
    return render_template('homescreen.html', message="Errore, modifica cancellata")


@app.route('/fantaAsta', methods=['POST', 'GET'])
def fanta_asta():

    giocatoriFADict= getGiocatori(True) # giocatoriDict[ruolo]= [id, nome, squadra, vI, vAtt]

    '''for key in giocatoriFADict.keys():

        print("player dentro fanta_asta: ", giocatoriFADict[key])'''

    # Leggo tutti i giocatori non appartenenti a fantasquadre come dizionario

    
    # Leggo tutte le squadre registrare. Nelle squadre lette ho anche l'id del fanta allenatore proprietario
    nomeTeam, idFantaAll, crediti, dictTeam= getFantaSquadre() # dictTeam{ 'idFantaAll:: Int': [TeamName, crediti:: Int] }

    # Leggo tutti i fanta allenatori    
    fantaAllenatoriDB= FantaAllenatore.query.all() # fantaAllenatoriDB= str(self.id) + '|' + self.email + '|' + self.username
    dict_fanta_Allenatori= {}
    for allenatore in fantaAllenatoriDB:
        element= str(allenatore).split('|')
        dict_fanta_Allenatori[int(element[0])]= element[2] # dict_fanta_Allenatori[int(idFantaAll)]= "nomeAll"

    # Creo dizionario Squadre/FantaAllenatore
    fanta_Squadre= {}
    for key_Team in dictTeam.keys():
        fanta_Squadre[dictTeam[key_Team][0]]= [dict_fanta_Allenatori[key_Team], dictTeam[key_Team][1]]   # fanta_Squadre[nomeTeam]= [nomeFanta_All, crediti]

    # Creo dizionario Giocatori
    dict_giocatori= getGiocatori(False) # giocatoreDict[int(player_id)]=  [nome,ruolo,squadra,int(valI),int(valA)]

    # DIZIONARI OTTENUTI 
    #
    # dictTeam['int(idFantaAll)]= [TeamName, int(crediti)] 
    # dict_fanta_Allenatori[int(idFantaAll)]= "nomeAll"
    # fanta_Squadre[nomeTeam]= [nomeFanta_All, crediti]
    # giocatoreDict[int(player_id)]=  [nome,ruolo,squadra,int(valI),int(valA)]

    # Aggiorno dizionario fanta_Squadre
    for teamName in fanta_Squadre.keys():
        nGiocatori_Ruolo= {}
        i = 0

        dictPlayers= getPlayersTeam(teamName) # dictPlayers[Ruolo]=[int(player_id), nome, squadra, int(valI), int(valA)]
        # Calcolo quanti giocatori per ruolo ha la squadra
        for el in ['P', 'D', 'C', 'A']:
            nGiocatori_Ruolo[el]= len(dictPlayers[el])

        fanta_Squadre[teamName].append(dictPlayers) # Da qui fanta_Squadre ha come terzo el il dizionario dei giocatori di quella squadra
        fanta_Squadre[teamName].append(nGiocatori_Ruolo) # Quarto el il dizionario con numerosità dei ruoli della squadra

    
                                                        # dict              dict
     # fanta_Squadre[nomeTeam]= [nomeFanta_All, crediti, dictPlayers, nGiocatori_Ruolo]

    return render_template('fanta_asta.html', fanta_Squadre= fanta_Squadre, giocatoriFADict= giocatoriFADict)

@app.route("/playerlist", methods=['GET'])
def playerlist():
    
    playersDB= getPlayersDB()
    teams= Squadra.query.all()

    return render_template('playerlist.html', data=playersDB, squadre=teams, user_image= full_filename)





# --------- Funzioni ------------------------------------------------------------------------------------------------------------------

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


def getIDs(element):
    ids= []
    print("Element: ", element)
    for el in element:
        strEl= str(el)
        result= strEl.split('|')
        ids.append(result[0])
    return ids


def CreateID(element):
    queryResult= element.query.all()
    ids= getIDs(queryResult)
    intIds= []
    for el in ids:
        intIds.append(int(el))

    if len(intIds) >= 10:
        return 'F'
    # Massimo 10 giocatori
    n= random.randint(0,10)

    while n in intIds:
        n = random.randint(0,10)
    # print('dentro create, n= ', n)
    return n

def getGiocatori(giocatoriFreeAgent):

    # giocatoriFreeAgent se settato a True mi restituisce i giocatori che non hanno FantaSquadra, se settato a False mi restituisce tutti i giocatori
    giocatoreDict= {'P': [],
                    'D': [],
                    'C': [],
                    'A': []
                }

    if giocatoriFreeAgent:
        giocatoriList= Giocatore.query.filter_by(nomeFantasquadra= None)

        for giocatore in giocatoriList:
            playerList= str(giocatore).split('|')
            giocatoreDict[playerList[2]].append([int(playerList[0]), playerList[1], playerList[3], int(playerList[4]), int(playerList[5])])    

        '''for key in giocatoreDict.keys():
            print("player dentro getGiocatori: ", giocatoreDict[key])'''

    else:

        giocatoriList= Giocatore.query.all()  # str(self.player_id) +'|' + self.nome + '|' + self.ruolo + '|' + self.squadra + '|' + str(self.valI) + '|' + str(self.valA)

        for giocatore in giocatoriList:
            playerList= str(giocatore).split('|')
            giocatoreDict[int(playerList[0])]= [playerList[1], playerList[2], playerList[3], int(playerList[4]), int(playerList[5])]  # giocatoreDict[player_id]=  [nome,ruolo,squadra,valI,valA]
        
    # Nel caso giocatoriFreeAgent sia true, la chiave del dizionario è il ruolo del giocatore
    return giocatoreDict

def getPlayersDB():
    playersDB= []
    players= Giocatore.query.all()
    for player in players:
        el= str(player)
        playerList= el.split('|')
        playersDB.append( [int(playerList[0]), playerList[1], playerList[2], playerList[3], int(playerList[4]), int(playerList[5])] )
    
    return playersDB




def getPlayersTeam(nomeTeam):
    dictTeam= {'P': [],
               'D': [],
               'C': [],
               'A': [] }
    
    giocatoriList= Giocatore.query.join(FantaSquadra)

    for el in giocatoriList:
        giocatore= str(el).strip('|')
        dictTeam[giocatore[2]].append([int(giocatore[0]), giocatore[1], giocatore[3], int(giocatore[4]), int(giocatore[5])])
    
    return dictTeam




def getFantaSquadre():
    nomeTeam= []
    idFantaAll= []
    crediti= []

    dictTeam= {}

    # self.TeamName + '|' + str(self.IdFantaAllenatore) + '|' + str(self.crediti)
    squadre= FantaSquadra.query.all()
    
    for squadra in squadre:
        team= str(squadra).split('|')
        dictTeam[int(team[1])]= [team[0], int(team[2])]   # dictTeam{ 'idFantaAll:: Int': [TeamName, crediti:: Int] }
        nomeTeam.append(team[0])
        idFantaAll.append(int(team[1]))
        crediti.append(int(team[2]))
    
    return nomeTeam, idFantaAll, crediti, dictTeam

def getFantaMisterDB():
    results= []
    joinResults= {}
    emails= []
    usernames= []    

    # fantaAllenatoriDB= str(self.id) + '|' + self.email + '|' + self.username
    fantaAllenatoriDB= FantaAllenatore.query.all()

    # FAllenatoreSquadraJoin= FantaAllenatore.query.join(FantaSquadra).filter(FantaAllenatore.id == FantaSquadra.IdFantaAllenatore)

    # Ottengo le fantasquadre(se presenti) relative ad ogni allenatore in modo da poterle mostrare nell'homescreen (si potrebbe fare anche con una selectaAll su FantaSquadre)
    fantaSquadreJoin= FantaSquadra.query.join(FantaAllenatore).filter(FantaAllenatore.id == FantaSquadra.IdFantaAllenatore)
    for res in fantaSquadreJoin:
        element= str(res).split('|')
                   # idFantaAll    nomeFantaTeam, Crediti
        joinResults[element[1]]= [element[0], element[2]]

    # Spezzo la rappresentazione di FantaAllenatore per l'elaborazione
    for allenatore in fantaAllenatoriDB:
        elements= str(allenatore).split('|')

        # Aggiungo le info sulla fantasquadra relativa all'utente in considerazione nel caso la fantasquadra esistesse
        if elements[0] in joinResults.keys():
            elements.append(joinResults[elements[0]][0])  # joinResults[idFantaAll][0]==NomeFantaSquadra
            # elements.append(joinResults[elements[0]][1]) # Crediti, non necessario aggiungerli
        else:
            elements.append('-')
            print("Chiave ", elements[0], " non presente nel dizionario")

        results.append(elements)

        emails.append(elements[1])
        usernames.append(elements[2])
    
    # print("results: ", results)
    return usernames, emails, results


# Inizializzo i dati nel DB leggendoli e sistemandoli dal file .csv
def initFileData():
    # Leggo file xslx contenente i dati di giocatori e squadre
    df= pd.read_csv(r'C:\Users\lucap\OneDrive\Desktop\Codici\FantaDB\FantaDB\Quotazioni_Fantacalcio.csv', skiprows=1)
    
    # Leggo le squadre già presenti nel DB all'avvio del programma
    teams= Squadra.query.all()
    
    # print(df)
    #------------------------ Init delle Squadre(SeriaA) nel DB-----------------------------------------------------------------------
    # Incomincio a inserire i nomi delle squadre di SerieA nel DB se non sono già presenti
    # Ho dovuto usare due liste di appoggio perchè nonostante nel model ho messo che squadre torna una stringa, non riuscivo a far la comparazione tra le squadre già presenti nel db 
    # e quelle lette dal file e mi dava errore perchè ogni volta che facevo partire il programma, 
    # il codice provava a reinserire tutte le squadre lette dal file .csv anche quelle già presenti nel DB dandomi quindi errore d'integrità 
    # perchè aggiungo qualcosa che è gia presente (il nome della squadra è l'unico attributo nonchè PK)

    readTeam= [] # Lista di team letti dal file csv
    strTeam= [] # Trasformo in Stringa le squadre lette dal DB

    # Inizializzo le due liste con cui opererò

    for el in teams:
        strTeam.append(str(el))

    for team in df['Squadra']: 
        if team not in readTeam:
            readTeam.append(str(team))

    # Per mantenere la lista squadre sempre aggiornate, una volta lette le squadre presenti nel DB e quelle lette dal file .csv, elimino le squadre presenti nel DB che non sono anche presenti nel file .csv letto
    # questo perchè se nel db ho squadre della stagione precedente che sono retrocesse, esse non saranno presenti nel file .csv della stagione corrente

    for team in strTeam:
        if team not in readTeam:
            Squadra.query.filter_by(nome=team).delete()
            try:
                db_session.commit()
            except exc.SQLAlchemyError as e:
                print("Error: ", e)

    #  print("Teams: ", strTeam)
    #  print("Team: ", readTeam)
    
    # Inserimento delle squadre mancanti lette dal .csv nel database
    for team in readTeam:
        if team not in strTeam:
            db_session.add(Squadra(team))
            try:
                db_session.commit()
            except exc.SQLAlchemyError as e:
                print("Error: ", e)

    #----------------------- Init dei giocatori nel DB---------------------------------------------------------------------------

    # print(df)       
    n= df['Id'].count() 
    # print('Numero giocatori: ', n)
    
    # Inizializzo le liste in cui inserirò i dati dei giocatori letti da .csv
    id_pl= []
    name_pl= []
    r= []
    sq_pl= []
    valI= []
    valAtt= []

    for element in df['Id']:
        id_pl.append(element)

    for element in df['R']:
        r.append(element)

    for element in df['Nome']:
        name_pl.append(element)
    
    for element in df['Squadra']:
        sq_pl.append(element)

    for element in df['Qt. A']:
        valI.append(element)

    for element in df['Qt. I']:
        valAtt.append(element)

    # Creo la lista dei giocatori con le loro info
    players= []
    
    i= 0
    for i in range(n):
        players.append([id_pl[i], name_pl[i], r[i], sq_pl[i], valI[i], valAtt[i]])
    
    # Leggo i giocatori gia presenti nel DB

    playersDB= getPlayersDB()

    # Come per le squadre, controllo che nella lista di giocatori salvati ne DB ci siano giocatori che siano anche nella lista di giocatori letta da .csv, questo perchè
    # tra un anno e l'altro alcuni giocatori possono essersene andati o possono essersi modificati alcuni dati
    for player in playersDB:
        # print("player: ", player)
        if player not in players:
            # print('player: ', player[0])
            Giocatore.query.filter_by(player_id=player[0]).delete()
            try:
                db_session.commit()
            except exc.SQLAlchemyError as e:
                print("Error: ", e)

    # Inserisco i giocatori mancanti nel DB
    for player in players:
        if player not in playersDB:
            db_session.add(Giocatore(player[0], player[1], player[2], player[3], player[4], player[5]))
            try:
                db_session.commit()
            except exc.SQLAlchemyError as e:
                print("Error: ", e)


if __name__ == "__main__":
    # Inizializzo il DB con tutte le sue tabelle
    init_db()
    
    initFileData()
    
    app.run()
