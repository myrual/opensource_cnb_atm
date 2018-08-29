from sqlalchemy import create_engine

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
class Person(Base):
    __tablename__ = 'person'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    userid = Column(String(250))
    name = Column(String(250), nullable=True)
    def __repr__(self):
        return "<Person(userid='%s', name='%s')>" % (
                                self.userid, self.name)


class GroupIncludeMe(Base):
    __tablename__ = 'group'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    conversation_idstring = Column(String(250))

    def __repr__(self):
        return "<Group of robot (converstion id ='%s')>" % (
                                self.conversation_idstring)
        
class TraceIdWithBattle(Base):
    __tablename__ = 'trace_id_battle'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    battle_id = Column(String(250))
    trace_id = Column(String(250))
    user_id = Column(String(250))
    snapshot_id = Column(String(250))
    asset_id = Column(String(250))
    asset_amount = Column(String(250))

    def __repr__(self):
        return "<Battle (battle id ='%s', trace_id: ='%s', user: ='%s')>" % (
                                self.battle_id, self.trace_id, self.user_id)
class Battle(Base):
    __tablename__ = 'battle_type_maxplayer'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    battle_id = Column(String(250))
    battle_type = Column(String(250))
    battle_maxPlayer = Column(Integer)

    def __repr__(self):
        return "<Battle (battle id ='%s', type: ='%s', maxPlayer: ='%d')>" % (
                                self.battle_id, self.battle_type, self.battle_maxPlayer)





class ToUserTransaction(Base):
    __tablename__ = 'rollbackTransaction'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    useridstring = Column(String(250))
    assetidstring = Column(String(250), nullable=True)
    amountstring = Column(String(250), nullable=True)

    def __repr__(self):
        return "<OpenTransaction(userid='%s', aasetid='%s', amountString ='%s')>" % (
                                self.useridstring, self.assetidstring, self.amountString)

class Freshman(Base):
    __tablename__ = 'freshmanbonus'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    userid = Column(String(250))
    bonusCounter = Column(Integer)
    def __repr__(self):
        return "<Person(userid='%s', bonusCounter='%d')>" % (
                                self.userid, self.bonusCounter)

