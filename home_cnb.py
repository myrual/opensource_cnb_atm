# -*- coding: utf-8 -*-
import web
import json
import requests
import jwt
import datetime
import calendar
import hashlib
import base64
import Crypto
import time
import uuid
import mixin_config
import sqlalchemy

from sqlalchemy import create_engine

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from database_type import *
engine = create_engine('sqlite:///sqlalchemy_example.db')
# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(engine)
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()



urls = (
    '/', 'index',
    '/auth','auth',
    '/CNB', 'balanceOfCNB',
    '/depositCNB','depositCNB',
    '/billionCNB','depositBillionCNB',
    '/millionCNB','depositMillionCNB'
)

class index:
    def GET(self):
        web.seeother('https://mixin.one/oauth/authorize?client_id=' + mixin_config.mixin_client_id + '&scope=PROFILE:READ')
class balanceOfCNB:
    def GET(self):
        raise web.seeother('https://mixin.one/oauth/authorize?client_id=3c5fd587-5ac3-4fb6-b294-423ba3473f7d&scope=PROFILE:READ')
    def GETlistAsset(self):
        raise web.seeother('https://mixin.one/oauth/authorize?client_id=3c5fd587-5ac3-4fb6-b294-423ba3473f7d&scope=PROFILE:READ+ASSETS:READ')

class depositCNB:
    def GET(self):
        raise web.seeother('https://mixin.one/pay?recipient=3c5fd587-5ac3-4fb6-b294-423ba3473f7d&asset=965e5c6e-434c-3fa9-b780-c50f43cd955c&amount=5000&trace=' + str(uuid.uuid1()) + '&memo=TEXT')

class depositBillionCNB:
    def GET(self):
        raise web.seeother('https://mixin.one/pay?recipient=3c5fd587-5ac3-4fb6-b294-423ba3473f7d&asset=965e5c6e-434c-3fa9-b780-c50f43cd955c&amount=' + str(10 * 10000 * 10000)+ '&trace=' + str(uuid.uuid1()) + '&memo=DepositeCNBV')


class depositMillionCNB:
    def GET(self):
        raise web.seeother('https://mixin.one/pay?recipient=3c5fd587-5ac3-4fb6-b294-423ba3473f7d&asset=965e5c6e-434c-3fa9-b780-c50f43cd955c&amount=' + str(1000 * 1000)+ '&trace=' + str(uuid.uuid1()) + '&memo=DepositeCNBV')




class auth:
    def GET(self):
        mixindata = web.input(code = "no")
	print(mixindata)
        if mixindata.code == "no":
            return "I don't know you, can not give your bonus"

        r = requests.post('https://api.mixin.one/oauth/token', json = {"client_id": mixin_config.mixin_client_id, "code": mixindata.code,"client_secret": mixin_config.mixin_client_secret})
        result = r.json()
	print(result)
        if "data" not in result or "access_token" not in result["data"]:
            return "I don't know you, can not give your bonus"
        access_token = result["data"]["access_token"]
        personinfo = requests.get('https://api.mixin.one/me', headers = {"Authorization":"Bearer " + access_token})
	mixin_userid = personinfo.json()["data"]["user_id"]
        mixin_username = personinfo.json()["data"]["full_name"]
        thisUserInORM = session.query(Person).filter_by(userid =hashlib.sha256(mixin_userid).hexdigest()).first() 
        if thisUserInORM == None:
            new_person = Person(name=mixin_username, userid = hashlib.sha256(mixin_userid).hexdigest())
            session.add(new_person)
            session.commit()
        else:
            thisUserInORM.username = mixin_username
            session.commit()
	print(personinfo.json())
        xin_asset_id = "c94ac88f-4671-3976-b60a-09064f1811e8"
        print("check my mixin assets")
        print(mixin_username.encode('utf-8'))
        cnb_asset_id = '965e5c6e-434c-3fa9-b780-c50f43cd955c'
        sendmessage_body = {}

        return u"Click X to close"
if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
