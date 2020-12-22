from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from FantaDB.database import Base
import random

# Da finire
class FantaSquadra(Base):
    __tablename__= 'FantaSquadre'
    
    TeamName= Column(String(20), primary_key=True, nullable=False)
    
    IdFantaAllenatore= Column(Integer, ForeignKey('FantaAllenatori.id'), unique=True, nullable=False)
    # allenatore= Column(String(20), ForeignKey('Allenatore.Nome'), unique=True, nullable=True)    
    crediti= Column(Integer, nullable= True)
    

    fantaAllenatore= relationship('FantaAllenatore')
    giocatore= relationship('Giocatore')
    # allenatore= relationship('Allenatore', back_populates='FantaSquadre')
    

    def __init__(self, teamName, IdFantaAllenatore):
        self.TeamName= teamName
        self.crediti= 300
        self.IdFantaAllenatore= IdFantaAllenatore


    def __repr__(self):
        return self.TeamName + '|' + str(self.IdFantaAllenatore) + '|' + str(self.crediti)




class FantaAllenatore(Base):
    __tablename__ = 'FantaAllenatori'
    id= Column(Integer, primary_key=True, nullable=False)
    email= Column(String(30), unique=True, nullable= True)
    username= Column(String(30), unique=True, nullable= False)
    fantaSquadra= relationship('FantaSquadra')


    def __init__(self, ID,  email, username):
        self.id = ID
        self.email= email
        self.username= username
    
    def __repr__(self):
        return  str(self.id) + '|' + self.email + '|' + self.username



        
'''class Allenatore(Base):
    __tablename__= 'allenatore'
    id_all= Column(Integer, primary_key= True, nullable=False)
    nome= Column(String(30), nullable=False)
    squadra= Column(String(30), nullable= False)
    # fantaSq_id= Column(Integer, ForeignKey('FantaSquadre.id'))
    # fantasquadra= relationship('FantaSquadra', back_populates='allenatore')
    # squadra= relationship('Squadra', back_populates="allenatore")
    
    def __init__(self, id, nome, squadra):
        self.nome= nome
        self.squadra= squadra
        self.id_all= id

    def __repr__(self):
        dictAll= {}
        dictAll['self.id_all']= [self.nome, self.squadra]
        return dictAll'''




class Squadra(Base):
    __tablename__= 'Squadre'
    nome= Column(String(30), primary_key= True, nullable=False)
    # nomeAll= Column(String(30), ForeignKey('allenatore.nome'))
    # allenatore= relationship('Allenatore', back_populates='squadra')

    def __init__(self, nome):
        self.nome= nome
    
    def __repr__(self):
        return str(self.nome)

class Giocatore(Base):
    __tablename__= 'Giocatori'

    player_id= Column(Integer, primary_key=True,  unique=True)
    nomeFantasquadra= Column(String(20), ForeignKey('FantaSquadre.TeamName'), nullable=True)

    nome= Column(String(50), unique=False, nullable=False)
    ruolo= Column(String(15), unique=False, nullable=False)
    squadra= Column(String(30), unique=False, nullable=False)

    valI= Column(Integer, unique=False, nullable=False)
    valA= Column(Integer, unique=False, nullable=False)
    valAcquisto= Column(Integer, unique=False, nullable=True)
    
    

    fantaTeam= relationship('FantaSquadra')

    def __init__(self, player_id, nome, ruolo, squadra, valI, valA, valAcq):
        self.player_id= int(player_id)
        self.nome= nome
        self.ruolo= ruolo
        self.squadra= squadra
        self.nomeFantasquadra= None
        self.valI= int(valI)
        self.valA= int(valA)
        self.valAcquisto= valAcq
    
    def __repr__(self):
        if self.nomeFantasquadra == None:
            return str(self.player_id) +'|' + self.nome + '|' + self.ruolo + '|' + self.squadra  + '|' + '-' + '|' + str(self.valI) + '|' + str(self.valA) + '|' + str(self.valAcquisto)
        else:
            return str(self.player_id) +'|' + self.nome + '|' + self.ruolo + '|' + self.squadra  + '|' + self.nomeFantasquadra + '|' + str(self.valI) + '|' + str(self.valA) + '|' + str(self.valAcquisto)
        # return [self.player_id, self.nome, self.ruolo, self.squadra, self.valI, self.valA]

