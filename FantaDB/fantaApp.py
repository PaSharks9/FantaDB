from flask import Flask, render_template,  request, redirect, url_for, flash

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Date, Integer, Text, create_engine, inspect, exc, join
from sqlalchemy.sql import select

from FantaDB.models import FantaAllenatore, Squadra, Giocatore, FantaSquadra, Allenatore
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


    # print("Mister presenti nel database: ", results)
    # POST suddiviso in più parti, la prima parte verifica se si arriva in post sulla home per cancellare dei fantallenatori, la seconda è per vedere se si arriva in post per aggiungere fantallenatori
    if request.method == 'POST':

        op= request.form['op']

        if op == 'delete':
            idForm=  request.form['Id']
            # print("idForm :", idForm)


            # Bisogna resettare l'attributo fantasquadra di tutti i giocatori facenti parte di questa fantasquadra in quanto è una chiave esterna verso la fantasquadra che si vuole cancellare
            fantaTeam= request.form['fantaTeam']
            giocatoriList= Giocatore.query.filter_by(nomeFantasquadra= fantaTeam).all()

            for player in giocatoriList:
                print("player: ", str(player))
                player.nomeFantasquadra= None
                db_session.add(player)
                db_session.commit()

            # Se il fantaAllenatore che vogliamo eliminare ha una fantasquadra prima eliminiamo questa poi lui (si potrebbe aggiungere che una volta eliminato l'utente, tutte le info relative a lui (compreso i suoi giocatori) vengono cancellate)
            # Avendo già effettuato una query e avendo ottenuto già i risultati riguardo i mister, non sto a reinterrogare il DB ma uso i dati che ho già letto
            for mister in results:
                if int(idForm) == int(mister[0]):
                    FantaSquadra.query.filter_by(IdFantaAllenatore= idForm).delete()
                    db_session.commit()

            FantaAllenatore.query.filter_by(id=idForm).delete()
            db_session.commit()
            return redirect('/')
        else:
            # Controllo il formato dell'email 
            # print("username :", request.form['username'])
            if request.form['Email'] != "" and request.form['username'] != "":
                print("email: ", request.form['Email'])
                if '@' not in request.form['Email'] or ('.it' not in request.form['Email'] and '.com' not in request.form['Email']):
                     return render_template('homescreen.html', data=results, user_image= full_filename, messages= "Formato email sbagliato, controllare che '@' o '.it' o '.com' siano presenti!")

                if request.form['Email'] not in emails and request.form['username'] not in usernames: 

                    IDmister= CreateID(FantaAllenatore)

                    if IDmister != 'F':
                        mister = FantaAllenatore(IDmister, request.form['Email'], request.form['username'])
                        db_session.add(mister)
                        db_session.commit()
                        return redirect('/')
                    else:
                        message= "Numero d'iscrizioni massimo raggiunto!"
                        render_template('homescreen.html', data=results, user_image= full_filename, messages= message)

                elif request.form['Email'] in emails: 
                    # flash("Username o Email già utilizzati!")
                    message= "Email già utilizzata!"
                    return render_template('homescreen.html', data=results, user_image= full_filename, messages= message)

                else:
                    message= "Username già utilizzato!"
                    return render_template('homescreen.html', data=results, user_image= full_filename, messages= message)
            else:
                return render_template('homescreen.html', data= results, user_image= full_filename, messages= "Inserire Username e/o Email!")
    
    return render_template('homescreen.html', data=results, user_image= full_filename, messages= "")


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
                return render_template('updateFAll.html', op=op, id=iD, nAllenatore= nameAllenatore, email= email, fantaT= 'y', dictTeam= dictTeam, messages= "" )

            # Se l'allenatore non ha una fantasquadra abilito la possibilità di aggiungerla 
            return render_template('updateFAll.html',op=op, id=iD, nAllenatore= nameAllenatore, email= email, fantaT= 'n', messages="")

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
                username= request.form['username']
                email= request.form['email']
                iD= request.form['iD']
                message= "Nome Squadra gia presente!"
                return render_template('updateFAll.html', messages= message, nAllenatore= username, email= email, fantaT= 'n', id= iD)
        
        elif op == "deleteFTeam":
            # Prima di cancellare la fantasquadra devo aggiornare la fantasquadra dei giocatori di quella fantasquadra
            giocatori= Giocatore.query.filter_by(nomeFantasquadra= request.form['nFTeam']).all()
            for player in giocatori: 
                player.nomeFantasquadra= None
                db_session.commit()

            FantaSquadra.query.filter_by(TeamName= request.form['nFTeam']).delete() # Volendo eventuale controllo su nFTeam dato che viene direttamente dalla form
            db_session.commit()
            return redirect('/')
        
        elif op == "updating":
            # Arrivo da updataFAll con i nuovi dati per effettuare la modifica
            iD= request.form['iD']
            nameAllenatore= request.form['username']
            emailAll= request.form['email']

            # Operazione di Update
            fAllenatore= FantaAllenatore.query.filter(FantaAllenatore.id == iD).one()
            fAllenatore.username= nameAllenatore
            fAllenatore.email= emailAll
            db_session.commit()
            # print("Utente modificato con successo")
            return redirect('/')

    
    return render_template('homescreen.html', messages="Errore, modifica cancellata")


@app.route('/fantaAsta', methods=['POST', 'GET'])
def fanta_asta():
    '''for el in request.form:

        print(el, ":", request.form[el]) '''

    if request.method == 'POST':

        response= False
        responseAll= False
        nome_FTeam= request.form['nomeFantaSquadra']
        op= request.form['op']
       
        # in entrambi devo fare le operazioni coi crediti
        if op == "del":
            
            selected_idPlayer= request.form['selected_idplayer']
            prezzo= request.form['prezzo']
            giocatore= Giocatore.query.filter_by(player_id= selected_idPlayer).first()

            giocatore.nomeFantasquadra= None
            response= calcola_crediti(prezzo, nome_FTeam, op, False)

        elif op == "add":

            prezzo= request.form['prezzo']
            selected_idPlayer= request.form['selected_idplayer']
            if selected_idPlayer == "Giocatori..." or prezzo == "Prezzo...":
                fanta_Squadre, giocatoriFA, allenatoriFA=  get_asta_view()
                return render_template('fanta_asta.html', fanta_Squadre= fanta_Squadre, giocatoriFADict= giocatoriFA, user_image= full_filename, allenatoriFA= allenatoriFA, messages="")
            

            giocatore= Giocatore.query.filter_by(player_id= selected_idPlayer).first()

            prezzo= int(prezzo)
            response= calcola_crediti(prezzo, nome_FTeam, op, False)
            giocatore.nomeFantasquadra= nome_FTeam
            giocatore.valAcquisto= prezzo

        elif op == "updtAll":
            print("dentro updtAll")
            prezzo= request.form['prezzo']
            nAllenatore= request.form['selected_allenatore']
            if nAllenatore == "Scegli..." or prezzo == "Prezzo..." :
                fanta_Squadre, giocatoriFA, allenatoriFA=  get_asta_view()
                return render_template('fanta_asta.html', fanta_Squadre= fanta_Squadre, giocatoriFADict= giocatoriFA, user_image= full_filename, allenatoriFA= allenatoriFA, messages="")

            team= FantaSquadra.query.filter_by(TeamName= nome_FTeam).first()
            responseAll= calcola_crediti(int(prezzo), nome_FTeam, 'add', True)
            team.allenatore= nAllenatore

        elif op == "delAll":

            nAllenatore= request.form['selected_allenatore']
            team= FantaSquadra.query.filter_by(TeamName= nome_FTeam).first()
            team.allenatore= None
            prezzo= team.valAcquistoAll
            responseAll= calcola_crediti(prezzo, nome_FTeam, 'del', True)

        if response:
            db_session.add(giocatore)
            db_session.commit()
        elif responseAll:
            db_session.add(team)
            db_session.commit()
        else: 
            fanta_Squadre, giocatoriFA, allenatoriFA=  get_asta_view()
            return render_template('fanta_asta.html', fanta_Squadre= fanta_Squadre, giocatoriFADict= giocatoriFA, user_image= full_filename, allenatoriFA= allenatoriFA, messages="Crediti Insufficenti!")
    '''allenatoriFA= getAllenatori(True)  # allenatori_FA[nomeall]= squadraAll
    giocatoriFA= getDictGiocatori(True) # giocatoriFA[ruolo]= [player_id, nome, squadra, fantasquadra, valI, valA]
    fanta_Squadre= get_fantaSquadre_dict() #  dictTeam[teamName]= [NomeFantaAll, fantaTeam_players, int(crediti), allenatore]'''

    fanta_Squadre, giocatoriFA, allenatoriFA=  get_asta_view()
    return render_template('fanta_asta.html', fanta_Squadre= fanta_Squadre, giocatoriFADict= giocatoriFA, user_image= full_filename, allenatoriFA= allenatoriFA, messages="")


@app.route("/playerlist", methods=['GET'])
def playerlist():
    
    playersDB= getDictGiocatori(False)
    teams= Squadra.query.all()

    '''for key in playersDB.keys():
        print("playersDB: ", playersDB[key])'''
    return render_template('playerlist.html', data=playersDB, squadre=teams, user_image= full_filename)



# --------- Funzioni ------------------------------------------------------------------------------------------------------------------

def calcola_crediti(prezzo, nomeTeam, op, allenatore):
    fanta_team= FantaSquadra.query.filter_by(TeamName= nomeTeam).first()

    # fantaAllenatoreJoin= FantaAllenatore.query.join(FantaSquadra).filter(FantaAllenatore.id == FantaSquadra.IdFantaAllenatore)
    if op == 'add':
        players= Giocatore.query.filter_by(nomeFantasquadra= nomeTeam)
        team= []
        for el in players:
            players_team= str(el).split('|')
            team.append(players_team)
            # print("players: ", str(el).split('|'))
        
        # Il prezzo d'acquisto inserito deve essere minore dei crediti residui della fantasquadra + 1 credito per ogni buco rimasto per giocatori e allenatore (squadre da 26)
        if fanta_team.crediti - int(prezzo) > 26 - len(team):
            fanta_team.crediti= fanta_team.crediti - int(prezzo)
            if allenatore:
                fanta_team.valAcquistoAll= prezzo
            db_session.add(fanta_team)
            db_session.commit()
            return True
        else:
            return False 

    elif op == 'del':  
        if fanta_team.crediti + int(prezzo) > 300:
            return Falses
        else:
            fanta_team.crediti= fanta_team.crediti + int(prezzo)
            db_session.add(fanta_team)
            db_session.commit()
            return True


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

def get_asta_view():
    allenatoriFA= getAllenatori(True)  # allenatori_FA[nomeall]= squadraAll
    giocatoriFA= getDictGiocatori(True) # giocatoriFA[ruolo]= [player_id, nome, squadra, fantasquadra, valI, valA]
    fanta_Squadre= get_fantaSquadre_dict() #  dictTeam[teamName]= [NomeFantaAll, fantaTeam_players, int(crediti), allenatore]
    return fanta_Squadre, giocatoriFA, allenatoriFA

# Come argomento va passato un modello del db, questa funzione effettua una query sul modello del db passato e ne restituisce un array di risultati
def getData(entity):
    entityList= []
    entityResults= entity.query.all()
    for el in entityResults:
        element = str(el)
        elementList= element.split('|')
        entityList.append(elementList)
    return entityList

# getFantaSquadre ---> updateFanta All
def getFantaSquadre():
    nomeTeam= []
    idFantaAll= []
    crediti= []

    dictTeam= {}

    # self.TeamName + '|' + str(self.IdFantaAllenatore) + '|' + str(self.crediti)
    squadre= FantaSquadra.query.all()
    
    for squadra in squadre:
        team= str(squadra).split('|')
        dictTeam[int(team[1])]= [team[0], int(team[2])]   #  dictTeam[int(idFantaAll)]= [TeamName, int(crediti)]
        nomeTeam.append(team[0])
        idFantaAll.append(int(team[1]))
        crediti.append(int(team[2]))
    
    return nomeTeam, idFantaAll, crediti, dictTeam


def get_fantaSquadre_dict():
    dictTeam= {}
    misterDict= {}


    # self.TeamName + '|' + str(self.IdFantaAllenatore) + '|' + str(self.crediti) + '|' + allenatore
    squadre= FantaSquadra.query.all()

    # str(self.id) + '|' + self.email + '|' + self.username
    fantaAllenatoreJoin= FantaAllenatore.query.join(FantaSquadra).filter(FantaAllenatore.id == FantaSquadra.IdFantaAllenatore)

   
    for mister in fantaAllenatoreJoin:
        mi= str(mister).split('|')
        misterDict[int(mi[0])]= mi[2]       # Creo dizionario dove la chiave è l'id e il valore è il nome del fanta_allenatore

    # print("fantaAllenatoreJoin :", str(misterList))
    for squadra in squadre:
        team= str(squadra).split('|')
        fantaTeam_players= getPlayersTeam(team[0]) # fantaTeam_players[ruolo]= player_id, nome, squadra, nomeFantasquadra, valI, valA  
        dictTeam[team[0]]= [misterDict[int(team[1])], fantaTeam_players, int(team[2]), team[3]]   #  dictTeam[teamName]= [NomeFantaAll, fantaTeam_players, int(crediti), allenatore]

    return dictTeam


def getPlayersTeam(nomeTeam):
    dictTeam= {'P': [],
               'D': [],
               'C': [],
               'A': [] }
    
    # player_id, nome, ruolo, squadra, nomeFantasquadra, valI, valA
    giocatoriList= Giocatore.query.join(FantaSquadra).filter(Giocatore.nomeFantasquadra == nomeTeam)

    
    for el in giocatoriList:
        giocatore= str(el).split('|')
        # print("el: ", str(el))
        # print("Giocatore dentro getPlayersTeam: ", giocatore)
        dictTeam[giocatore[2]].append([int(giocatore[0]), giocatore[1], giocatore[3], giocatore[4], int(giocatore[5]), int(giocatore[6]), int(giocatore[7])])
    
    return dictTeam

# getFantaMisterDB ---> home
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
        joinResults[element[1]]= [element[0], element[2], element[3]]

    # Spezzo la rappresentazione di FantaAllenatore per l'elaborazione
    for allenatore in fantaAllenatoriDB:
        elements= str(allenatore).split('|')

        # Aggiungo le info sulla fantasquadra relativa all'utente in considerazione nel caso la fantasquadra esistesse
        if elements[0] in joinResults.keys():
            elements.append(joinResults[elements[0]][0])  # joinResults[idFantaAll][0]==NomeFantaSquadra
            # elements.append(joinResults[elements[0]][1]) # Crediti, non necessario aggiungerli
        else:
            elements.append('-') # fantaAllenatore= id, email, username, fantasquadra
            print("Chiave ", elements[0], " non presente nel dizionario")

        results.append(elements)

        emails.append(elements[1])
        usernames.append(elements[2])
    
    # print("results: ", results)
    return usernames, emails, results



# giocatoriFreeAgent se settato a True mi restituisce un dizionario con tutti i giocatori free agent, chiave del dizionario il ruolo
# Se giocatoriFreeAgent settato a False mi restituisce un dizionario con tutti i giocatori (senza fantasquadra), con chiave l'id del player
def getDictGiocatori(giocatoriFreeAgent):

    if giocatoriFreeAgent:
        giocatoreDict= {
            'P': [],
            'D': [],
            'C': [],
            'A': []
        }

        giocatoriList= Giocatore.query.filter_by(nomeFantasquadra= None)

        for giocatore in giocatoriList:
            playerList= str(giocatore).split('|')
            giocatoreDict[playerList[2]].append([int(playerList[0]), playerList[1], playerList[3], playerList[4], int(playerList[5]), int(playerList[6])])    

        '''for key in giocatoreDict.keys():
            print("player dentro getGiocatori: ", giocatoreDict[key])'''

    else:
        giocatoreDict=  {}
        # Usato nell'init, quindi tolgo fantasquadra
        giocatoriList= Giocatore.query.all()  # str(self.player_id) +'|' + self.nome + '|' + self.ruolo + '|' + self.squadra + '|' + self.fantasquadra + '|' + str(self.valI) + '|' + str(self.valA)

        for giocatore in giocatoriList:
            playerList= str(giocatore).split('|')
            giocatoreDict[int(playerList[0])]= [playerList[1], playerList[2], playerList[3], int(playerList[5]), int(playerList[6])]  # giocatoreDict[player_id]=  [nome,ruolo,squadra,valI,valA]
        
    return giocatoreDict


def getAllenatori(allenatoriFreeAgent):

    allenatoriDictDB= {} # dizionario dove sono presenti tutti gli allenatori nel db, free agent o no
    allenatoriDB= Allenatore.query.all()

    for el in allenatoriDB:
        allenatore= str(el).split('|') 
        allenatoriDictDB[allenatore[0]]= allenatore[1]

    if allenatoriFreeAgent:  # se è true sto chiedendo un dizionario di allenatori senza una fanta squadra assegnata

        allenatori_FA=  {}  # allenatori free agent, ovvero non appartenenti a nessuna fanta squadra

        fantaSq_List= FantaSquadra.query.join(Allenatore).filter(FantaSquadra.allenatore == Allenatore.nome)
        fantaSq_All= [] # lista con presente tutti i nomi degli allenatori assegnati ad una fantasquadra
        for el in fantaSq_List:
            fantaSq= str(el).split('|')
            fantaSq_All.append(fantaSq[3])

        for key in allenatoriDictDB.keys(): # la chiave di questo dizionario è il nome dell'allenatore (che essendo nome e cognome è univoco (quasi sempre))
            if key not in fantaSq_All:
                allenatori_FA[key]= allenatoriDictDB[key]

        return allenatori_FA # allenatori_FA[nomeall]= squadraAll

    else:
        return allenatoriDictDB  # allenatoriDictDB[nomeall] = squadraAll       # la squadra dell'allenatore è la squadra reale NON la fantasquadra


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
    giocatoriList=[]
    giocatoriDB= Giocatore.query.all()
    for el in giocatoriDB:
        giocatoriList.append(str(el).split('|')) 

    if len(giocatoriList) == 0:

        # print(df)       
        n= df['Id'].count() 
        i = 0
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

        for i in range(n):
            giocatore= Giocatore(id_pl[i], name_pl[i], r[i], sq_pl[i], valI[i], valAtt[i], 0)
            db_session.add(giocatore)
            db_session.commit()
    else:
        print("Giocatori gia inseriti")
    # ----------------------------------- Lettura Allenatori ------------------------------------------------------------------------ 
    # df= pd.read_csv(r'C:\Users\lucap\OneDrive\Desktop\Codici\FantaDB\FantaDB\Quotazioni_Fantacalcio.csv', skiprows=1)
    dfAll= pd.read_csv(r'C:\Users\lucap\OneDrive\Desktop\Codici\FantaDB\FantaDB\allenatori2020\21.csv')
    allenatoreList= []
    allenatoreDB= Allenatore.query.all()
    for mister in allenatoreDB:
        allenatoreList.append(str(mister).split('|'))
    n= dfAll['Allenatore'].count()

    if  len(allenatoreList) == 0: 
        nomeAll= []
        squadra_All= []

        for el in dfAll['Allenatore']:
            nomeAll.append(el)
        
        for el in dfAll['Squadra']:
            squadra_All.append(el)

        for i in range(n):
            allenatore= Allenatore(nomeAll[i], squadra_All[i])
            db_session.add(allenatore)
            db_session.commit()
    else:
        print("Allenatori già inseriti")

if __name__ == "__main__":
    # Inizializzo il DB con tutte le sue tabelle
    init_db()
    
    initFileData()
    
    app.run()



