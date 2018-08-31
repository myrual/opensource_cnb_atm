# -*- coding: utf-8 -*-
import websocket
import requests
import json
import ssl
from mixin_api import MIXIN_API
import uuid
import zlib
import gzip
from cStringIO import StringIO
import base64
import mixin_config
import mixin_asset_list
import random
import datetime
import hashlib
from operator import itemgetter
try:
    import thread
except ImportError:
    import _thread as thread
import time
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


ly_assetid = "35f7a3a3-4335-3bf3-beca-685836602d72"
btccash_asset_id = "fd11b6e3-0b87-41f1-a41f-f0e9b49e5bf0"

payAmount = 1
payAmountCNB = 1234567
bonusAmp = 3

bonusUnitText = 'CNB'
bonusAssetID = mixin_asset_list.CNB_ASSET_ID
colorOfCNB ="#fccf40"
colorOfCANDY ="#f40696"


battleAmount =  1688168
battleAssetName = u"吹牛大赛"
battleAssetID   = mixin_asset_list.CNB_ASSET_ID
battle_alreadyText  = u"已吹"



PER_PRS = "1"
PER_EOS = "0.017"
PER_SIA = "40"
PER_XIN = "0.0002"

CNB_PER_PRS = "12345678"
PER_CNB = "12345678"
PRS_PER_CNB = "0.0001"
PER_CANDY = "1"

MAX_PLAYER_BATTLE = 3

freeBonusTimeTable = {}
latestPlayersStatus= {}

latestChatterStatus= {}
latestOnlinePlayers = []
latestPlayersScore = {}
latestBuyers = {}
latestSellers = {}


totalWinner = 0

totalCNBBuyBack= 0
admin_conversation_id = ""

mixin_api_robot = MIXIN_API()
mixin_api_robot.appid = mixin_config.mixin_client_id
mixin_api_robot.secret = mixin_config.mixin_client_secret
mixin_api_robot.sessionid = mixin_config.mixin_pay_sessionid
mixin_api_robot.private_key = mixin_config.private_key
mixin_api_robot.asset_pin = mixin_config.mixin_pay_pin
mixin_api_robot.pin_token = mixin_config.mixin_pin_token
myConfig  = mixin_config.user_mixin_config()
myConfig.mixin_client_id = mixin_config.mixin_client_id 
myConfig.mixin_pay_sessionid = mixin_config.mixin_pay_sessionid 
myConfig.mixin_pin_token = mixin_config.mixin_pin_token
myConfig.private_key = mixin_config.private_key
myConfig.deviceID = myConfig.mixin_client_id
myConfig.asset_pin = mixin_config.mixin_pay_pin


groupOfFighters = []

groupOfChat = {}

def listAssets(robot, config):
    encoded = robot.genGETJwtToken_extConfig('/assets', "", config)
    r = requests.get('https://api.mixin.one/assets', headers = {"Authorization":"Bearer " + encoded, "Mixin-Device-Id":config.mixin_client_id})
    print(r.status_code)
    if r.status_code != 200:
        error_body = result_obj['error']
        print(error_body)

    r.raise_for_status()

    result_obj = r.json()
    print(result_obj)
    assets_info = result_obj["data"]
    asset_list = []
    for singleAsset in assets_info:
        if singleAsset["balance"] != "0":
            asset_list.append((singleAsset["symbol"], singleAsset["balance"]))
    return asset_list
def listCNBPRSAssets(robot, config):
    result = {}
    result["CNB"] = 0.0
    result["PRS"] = 0.0
    encoded = robot.genGETJwtToken_extConfig('/assets', "", config)
    r = requests.get('https://api.mixin.one/assets', headers = {"Authorization":"Bearer " + encoded, "Mixin-Device-Id":config.mixin_client_id})
    print(r.status_code)
    if r.status_code != 200:
        error_body = result_obj['error']
        print(error_body)

    r.raise_for_status()

    result_obj = r.json()
    assets_info = result_obj["data"]
    for singleAsset in assets_info:
        if singleAsset["asset_id"] == mixin_asset_list.CNB_ASSET_ID:
            result["CNB"] = singleAsset["balance"]
        if singleAsset["asset_id"] == mixin_asset_list.PRS_ASSET_ID:
            result["PRS"] = singleAsset["balance"]
    return result

def transferTo(robot, config, to_user_id, to_asset_id,to_asset_amount,memo):
    encrypted_pin = robot.genEncrypedPin_extConfig(config)
    body = {'asset_id': to_asset_id, 'counter_user_id':to_user_id, 'amount':str(to_asset_amount), 'pin':encrypted_pin, 'trace_id':str(uuid.uuid1())}
    body_in_json = json.dumps(body)

    encoded = robot.genPOSTJwtToken_extConfig('/transfers', body_in_json, config)
    r = requests.post('https://api.mixin.one/transfers', json = body, headers = {"Authorization":"Bearer " + encoded})
    result_obj = r.json()
    if 'error' in result_obj:
        error_body = result_obj['error']
        error_code = error_body['code']
        print("to :" + to_user_id + " with asset:" + to_asset_id + " amount:" + str(to_asset_amount))
        print(result_obj)
	if error_code == 20119:
            transferTo(robot, config, to_user_id, to_asset_id,to_asset_amount,memo)
        return False
    else:
        return True

def writeMessage(websocketInstance, action, params):
    Message = {"id":str(uuid.uuid1()), "action":action, "params":params}
    Message_instring = json.dumps(Message)
    fgz = StringIO()
    gzip_obj = gzip.GzipFile(mode='wb', fileobj=fgz)
    gzip_obj.write(Message_instring)
    gzip_obj.close()
    websocketInstance.send(fgz.getvalue(), opcode=websocket.ABNF.OPCODE_BINARY)


def sendUserAppButton(websocketInstance, in_conversation_id, to_user_id, realLink, text4Link, colorOfLink = "#d53120"):
    btnJson = json.dumps([{"label":text4Link, "action":realLink, "color":colorOfLink}])
    params = {"conversation_id": in_conversation_id,"recipient_id":to_user_id,"message_id":str(uuid.uuid4()),"category":"APP_BUTTON_GROUP","data":base64.b64encode(btnJson)}
    return writeMessage(websocketInstance, "CREATE_MESSAGE",params)

def sendUserContactCard(websocketInstance, in_conversation_id, to_user_id, to_share_userid):
    btnJson = json.dumps({"user_id":to_share_userid})
    params = {"conversation_id": in_conversation_id,"recipient_id":to_user_id,"message_id":str(uuid.uuid4()),"category":"PLAIN_CONTACT","data":base64.b64encode(base64.b64encode(btnJson))}
    return writeMessage(websocketInstance, "CREATE_MESSAGE",params)

def sendUserSticker(websocketInstance, in_conversation_id, to_user_id, album_id, sticker_name):
    realStickerObj = {}
    realStickerObj['album_id'] = album_id
    realStickerObj['name'] = sticker_name

    btnJson = json.dumps(realStickerObj)
    params = {"conversation_id": in_conversation_id,"recipient_id":to_user_id,"message_id":str(uuid.uuid4()),"category":"PLAIN_STICKER","data":base64.b64encode(base64.b64encode(btnJson))}
    return writeMessage(websocketInstance, "CREATE_MESSAGE",params)


def sendUserGameEntrance(webSocketInstance, in_config, in_conversation_id, to_user_id, in_link_text, inAssetID, inPayAmount, linkColor = "#0CAAF5", memotext = 'PRS2CNB', trace_id = ""):
    if trace_id == "":
        payLink = "https://mixin.one/pay?recipient=" + in_config.mixin_client_id + "&asset=" + inAssetID + "&amount=" + str(inPayAmount) + '&trace=' + str(uuid.uuid1()) + '&memo=' + memotext

        btn = '[{"label":"' + in_link_text + '","action":"' + payLink + '","color":"' + linkColor + '"}]'
        gameEntranceParams = {"conversation_id": in_conversation_id,"recipient_id":to_user_id,"message_id":str(uuid.uuid4()),"category":"APP_BUTTON_GROUP","data":base64.b64encode(btn)}
        writeMessage(webSocketInstance, "CREATE_MESSAGE",gameEntranceParams)
        return
    else:
        payLink = "https://mixin.one/pay?recipient=" + in_config.mixin_client_id + "&asset=" + inAssetID + "&amount=" + str(inPayAmount) + '&trace=' + trace_id + '&memo=' + memotext
        btn = u'[{"label":"'.encode('utf-8') + in_link_text + u'","action":"'.encode('utf-8') + payLink.encode('utf-8') + u'","color":"'.encode('utf-8') + linkColor.encode('utf-8') + u'"}]'.encode('utf-8')
        gameEntranceParams = {"conversation_id": in_conversation_id,"recipient_id":to_user_id,"message_id":str(uuid.uuid4()),"category":"APP_BUTTON_GROUP","data":base64.b64encode(btn)}
        writeMessage(webSocketInstance, "CREATE_MESSAGE",gameEntranceParams)
        return

def sendGroupGameEntrance(webSocketInstance, in_config, in_conversation_id, in_link_text, inAssetID, inPayAmount, linkColor = "#0CAAF5", memotext = 'PRS2CNB', trace_id = ""):
    if trace_id == "":
        payLink = "https://mixin.one/pay?recipient=" + in_config.mixin_client_id + "&asset=" + inAssetID + "&amount=" + str(inPayAmount) + '&trace=' + str(uuid.uuid1()) + '&memo=' + memotext

        btn = '[{"label":"' + in_link_text + '","action":"' + payLink + '","color":"' + linkColor + '"}]'
        gameEntranceParams = {"conversation_id": in_conversation_id,"message_id":str(uuid.uuid4()),"category":"APP_BUTTON_GROUP","data":base64.b64encode(btn)}
        writeMessage(webSocketInstance, "CREATE_MESSAGE",gameEntranceParams)
        return
    else:
        payLink = "https://mixin.one/pay?recipient=" + in_config.mixin_client_id + "&asset=" + inAssetID + "&amount=" + str(inPayAmount) + '&trace=' + trace_id + '&memo=' + memotext
        btn = u'[{"label":"'.encode('utf-8') + in_link_text + u'","action":"'.encode('utf-8') + payLink.encode('utf-8') + u'","color":"'.encode('utf-8') + linkColor.encode('utf-8') + u'"}]'.encode('utf-8')
        gameEntranceParams = {"conversation_id": in_conversation_id,"message_id":str(uuid.uuid4()),"category":"APP_BUTTON_GROUP","data":base64.b64encode(btn)}
        writeMessage(webSocketInstance, "CREATE_MESSAGE",gameEntranceParams)
        return



sendUserPayAppButton = sendUserGameEntrance

def sendUserText(websocketInstance, in_conversation_id, to_user_id, textContent):
    params = {"conversation_id": in_conversation_id,"recipient_id":to_user_id ,"message_id":str(uuid.uuid4()),"category":"PLAIN_TEXT","data":base64.b64encode(textContent)}
    return writeMessage(websocketInstance, "CREATE_MESSAGE",params)

def sendGroupText(websocketInstance, in_conversation_id, textContent):
    params = {"conversation_id": in_conversation_id,"message_id":str(uuid.uuid4()),"category":"PLAIN_TEXT","data":base64.b64encode(textContent)}
    return writeMessage(websocketInstance, "CREATE_MESSAGE",params)

def sendGroupAppButton(websocketInstance, in_conversation_id, realLink, text4Link, colorOfLink = "#d53120"):
    btnJson = json.dumps([{"label":text4Link, "action":realLink, "color":colorOfLink}])
    params = {"conversation_id": in_conversation_id, "message_id":str(uuid.uuid4()),"category":"APP_BUTTON_GROUP","data":base64.b64encode(btnJson)}
    return writeMessage(websocketInstance, "CREATE_MESSAGE",params)

def sendGroupPay(webSocketInstance, in_config, in_conversation_id, inAssetName, inAssetID, inPayAmount, linkColor = "#0CAAF5", ):
    payLink = "https://mixin.one/pay?recipient=" + in_config.mixin_client_id + "&asset=" + inAssetID + "&amount=" + str(inPayAmount) + '&trace=' + str(uuid.uuid1()) + '&memo=PRS2CNB'
    btn = '[{"label":"' + inAssetName + '","action":"' + payLink + '","color":"' + linkColor + '"}]'
    gameEntranceParams = {"conversation_id": in_conversation_id,"message_id":str(uuid.uuid4()),"category":"APP_BUTTON_GROUP","data":base64.b64encode(btn)}
    writeMessage(webSocketInstance, "CREATE_MESSAGE",gameEntranceParams)
    return



def showReceipt(websocketInstance, inConversationID, reply_user_id, reply_snapShotID):
    payLink = "https://mixin.one/snapshots/" + reply_snapShotID
    shortSnapShort = reply_snapShotID[0:13] + "..."
    btn = '[{"label":"Your receipt:' + shortSnapShort + '","action":"' + payLink + '","color":"#0CAAF5"}]'

    params = {"conversation_id": inConversationID,"recipient_id":reply_user_id,"message_id":str(uuid.uuid4()),"category":"APP_BUTTON_GROUP","data":base64.b64encode(btn)}
    writeMessage(websocketInstance, "CREATE_MESSAGE",params)

def replayMessage(websocketInstance, msgid):
    parameter4IncomingMsg = {"message_id":msgid, "status":"READ"}
    Message = {"id":str(uuid.uuid1()), "action":"ACKNOWLEDGE_MESSAGE_RECEIPT", "params":parameter4IncomingMsg}
    Message_instring = json.dumps(Message)
    fgz = StringIO()
    gzip_obj = gzip.GzipFile(mode='wb', fileobj=fgz)
    gzip_obj.write(Message_instring)
    gzip_obj.close()
    websocketInstance.send(fgz.getvalue(), opcode=websocket.ABNF.OPCODE_BINARY)



    return
replyMessage = replayMessage
def tryLucky(webSocketInst, in_msgid, in_snapshot_id, in_conversation_id, in_userid, robot, config, input_asset_id, float_bonus_amount, float_pay_amount):
    global totalWinner
    if mostLeftNumberGreaterThan6(in_snapshot_id):
        if transferTo(robot, config, in_userid, input_asset_id ,str(float_bonus_amount),"Winner"):
            totalWinner = totalWinner + 1

            realLink = u"https://mixin.one/snapshots/".encode('utf-8') + in_snapshot_id.encode('utf-8')
            realText = u"抽到".encode('utf-8') + mostLeftNumber(in_snapshot_id).encode('utf-8') +  u"，比6大".encode('utf-8')
            sendUserAppButton(webSocketInst, in_conversation_id, in_userid, realLink, realText, colorOfLink = "#ffd700")

        else:#balance is not enough
            transferTo(robot, config, in_userid, input_asset_id,str(float_pay_amount),"Winner")
            sendUserText(webSocketInst, in_conversation_id, in_userid, u"您是赌神，没钱了，不玩了，不玩了".encode('utf-8'))
    else:
        realLink = "https://mixin.one/snapshots/" + in_snapshot_id
        realText = u"抽到".encode('utf-8') + mostLeftNumber(in_snapshot_id).encode('utf-8') +  u"，比7小".encode('utf-8')
        sendUserAppButton(webSocketInst, in_conversation_id, in_userid, realLink, realText, colorOfLink = "#000000")

def mostLeftNumber(toCompareString):
    for each in toCompareString:
        if each.isdigit():
            return each
    return ''

def mostLeftNumberGreaterThan6(toCompareString):
    for each in toCompareString:
        if each.isdigit():
            if each == '7' or each == '8' or each == '9':
                return True
            return False
    return False
def userNameInDataBase(user_id):
    hashOfUserID = hashlib.sha256(user_id).hexdigest()
    return session.query(Person).filter_by(userid =hashOfUserID).first()

def addOneGroup(in_conversion_id):
    toAddGroup = session.query(GroupIncludeMe).filter_by(conversation_idstring = in_conversion_id).first()
    if toAddGroup == None:
        toAddOrm = GroupIncludeMe(conversation_idstring = in_conversion_id)
        session.add(toAddOrm)
        session.commit()
        return
    return

def removeOneGroup(in_conversion_id):
    toRemoveGroup = session.query(GroupIncludeMe).filter_by(conversation_idstring = in_conversion_id).first()
    if toRemoveGroup == None:
        return
    session.delete(toRemoveGroup)
    session.commit()

def allGroupsOfRobot():
    allGroupORM = session.query(GroupIncludeMe).all()
    result_list = []
    for eachGroup in allGroupORM:
        result_list.append(eachGroup.conversation_idstring)
    return result_list

def generateTraceIDForNextChallenger(in_battle_id, dbSession):
    nextTraceInBattle = TraceIdWithBattle()
    nextTraceInBattle.user_id = "" 
    nextTraceInBattle.trace_id = str(uuid.uuid1())
    nextTraceInBattle.battle_id = in_battle_id
    dbSession.add(nextTraceInBattle)
    dbSession.commit()
    return nextTraceInBattle.trace_id

def userCreateBattle(in_user_id, in_trace_id, in_snapshot_id, in_asset_id, in_asset_amount, dbSession, in_battle_type = "BigSmall", in_battle_maxPlayer = 2):
    newBattle = Battle()
    newBattle.battle_type = in_battle_type
    newBattle.battle_maxPlayer= in_battle_maxPlayer
    newBattle.battle_id = str(uuid.uuid1())
    dbSession.add(newBattle)
    dbSession.commit()

    newBattleTraceID = TraceIdWithBattle()
    newBattleTraceID.user_id = in_user_id
    newBattleTraceID.trace_id = in_trace_id
    newBattleTraceID.battle_id = newBattle.battle_id
    newBattleTraceID.snapshot_id = in_snapshot_id
    newBattleTraceID.asset_id = in_asset_id
    newBattleTraceID.asset_amount = in_asset_amount
    dbSession.add(newBattleTraceID)
    dbSession.commit()
   
    return newBattle.battle_id

def isUserPayToJoinBattle(in_trace_id, dbSession):
    userInBattleRecord = dbSession.query(TraceIdWithBattle).filter_by(user_id = "").filter_by(trace_id = in_trace_id).order_by(TraceIdWithBattle.id.desc()).first()
    return userInBattleRecord != None

def userDidJoinBattle(in_user_id, in_trace_id, in_snapshot_id, in_asset_id, in_asset_amount, dbSession):
    emptyUserBattleTrace = dbSession.query(TraceIdWithBattle).filter_by(user_id = "").filter_by(trace_id = in_trace_id).order_by(TraceIdWithBattle.id.desc()).first()
    emptyUserBattleTrace.user_id = in_user_id
    emptyUserBattleTrace.snapshot_id = in_snapshot_id
    emptyUserBattleTrace.asset_id = in_asset_id
    emptyUserBattleTrace.asset_amount = in_asset_amount
    dbSession.commit()
    return emptyUserBattleTrace.battle_id

def stillOpenBattleInTable(dbSession):
    theFirstOpenBattleTraceID = dbSession.query(TraceIdWithBattle).filter(TraceIdWithBattle.user_id == "").order_by(TraceIdWithBattle.id.desc()).first()
    return theFirstOpenBattleTraceID

def maxPlayerOfBattle(in_battle_id, dbSession):
    battle_info = dbSession.query(Battle).filter_by(battle_id = battle_id_of_thisRecord).first()
    return battle_info.battle_maxPlayer

def remainSeatInTable(in_battle_id, dbSession):
    battle_id_of_thisRecord = in_battle_id
    total_user_in_battle = len(dbSession.query(TraceIdWithBattle).filter_by(battle_id = battle_id_of_thisRecord).filter(TraceIdWithBattle.user_id != "").all())
    battle_info = dbSession.query(Battle).filter_by(battle_id = battle_id_of_thisRecord).first()
    return battle_info.battle_maxPlayer - total_user_in_battle

def calculateBattelResult(in_battle_id, dbSession, in_robot, in_config, in_commit_loser = ""):
    thisBattle = dbSession.query(Battle).filter_by(battle_id = in_battle_id).first()
    print(in_battle_id)
    if thisBattle.battle_type == "BigSmall":
        allUserPayForBattle = dbSession.query(TraceIdWithBattle).filter_by(battle_id = in_battle_id).all()
        firstBatchPaidUser = allUserPayForBattle[:thisBattle.battle_maxPlayer]
        resultOfAllUserPayFor = {}

        #[
        # {"userid":"user1", "dice_number":1, "asset_id":"cnb_", "asset_amount":"123},
        # {"userid":"user2", "dice_number":2, "asset_id":"cnb_", "asset_amount":"123}
        #]

        for eachUserRecord in firstBatchPaidUser:
            resultOfAllUserPayFor[eachUserRecord.user_id] = {"dice_number":int(mostLeftNumber(eachUserRecord.snapshot_id)), "asset_id":eachUserRecord.asset_id, "asset_amount":0}
            print(resultOfAllUserPayFor[eachUserRecord.user_id])

        for eachUserID in resultOfAllUserPayFor.keys():
            allPayForEachUser = dbSession.query(TraceIdWithBattle).filter_by(battle_id = in_battle_id).filter_by(user_id = eachUserID).all()
            totalAmount = 0
            for eachPayForEachUser in allPayForEachUser:
                totalAmount = totalAmount + float(eachPayForEachUser.asset_amount)
            resultOfAllUserPayFor[eachUserID] = {"dice_number":resultOfAllUserPayFor[eachUserID]["dice_number"], "asset_id":resultOfAllUserPayFor[eachUserID]["asset_id"], "asset_amount":totalAmount}
        #[
        # {"userid":"user1", "dice_number":1, "asset_id":"cnb_", "asset_amount":"123+123},
        # {"userid":"user2", "dice_number":2, "asset_id":"cnb_", "asset_amount":"123+123}
        #]


        result = []
        for eachWinner in resultOfAllUserPayFor:
            result.append((eachWinner, resultOfAllUserPayFor[eachWinner]["dice_number"]))
        #
        #[
        # ("user1", 1),
        # ("user2", 2),
        #]
        sorted_list = sorted(result, key=lambda tup: tup[1], reverse = True)
        #
        #[
        # ("user2", 2),
        # ("user1", 1),
        #]

        firstWinner = sorted_list[0]
        winner_list = [firstWinner]
        loser_list = []
        for eachRemainPlayer in sorted_list[1:]:
            if firstWinner[1] > eachRemainPlayer[1]:
                loser_list.append(eachRemainPlayer)
            else:
                winner_list.append(eachRemainPlayer)
        print("winner list")
        print(winner_list)
        totalLoseAmount = 0.0
        for eachLoser in loser_list:
            loserID = eachLoser[0]
            totalLoseAmount = totalLoseAmount + resultOfAllUserPayFor[loserID]["asset_amount"]
        print("loser list")
        print(loser_list)

        totalLoseAmount = totalLoseAmount * 0.95
        totalWinner = len(winner_list)
        eachBonus = (totalLoseAmount ) /(totalWinner * 1.0)

        for eachWinner in winner_list:
            winnerID = eachWinner[0]
            winnerPaidAmount = resultOfAllUserPayFor[winnerID]["asset_amount"]
            toWinnerAmount = winnerPaidAmount + eachBonus
            transferTo(in_robot, in_config, winnerID, resultOfAllUserPayFor[winnerID]["asset_id"],str(toWinnerAmount),"Winner")

        #find out max dice first
        #insert to winner group
        #loop all remain and compare with winner
        #now resultOfAllUserPayFor has user id, dice_number, and all money
        return sorted_list
    else:
        return
    return total_user_in_battle == battle_info.battle_maxPlayer


def isUserJoinBattle(in_user_id, in_trace_id, dbSession):
    userInBattleRecord = dbSession.query(TraceIdWithBattle).filter_by(user_id = in_user_id).filter_by(trace_id = in_trace_id).last()
    return userInBattleRecord != None



def removeOneGroup(in_conversion_id):
    toRemoveGroup = session.query(GroupIncludeMe).filter_by(conversation_idstring = in_conversion_id).first()
    if toRemoveGroup == None:
        return
    session.delete(toRemoveGroup)
    session.commit()

def allGroupsOfRobot():
    allGroupORM = session.query(GroupIncludeMe).all()
    result_list = []
    for eachGroup in allGroupORM:
        result_list.append(eachGroup.conversation_idstring)
    return result_list

def userNameOrHashOrIDInDataBase(user_id):
    userInORM =  userNameInDataBase(user_id)
    hashOfUserID = hashlib.sha256(user_id).hexdigest()

    if userInORM == None:
        return hashOfUserID.encode('utf-8')
    else:
        return userInORM.name

def recordCNBBuyer(in_userid):
    global latestBuyers
    if in_userid in latestBuyers:
        latestBuyers[in_userid] =  latestBuyers[in_userid] + 1
    else:
        latestBuyers[in_userid] =  1
    return
def recordCNBSeller(in_userid):
    global latestSellers
    if in_userid in latestSellers:
        latestSellers[in_userid] =  latestSellers[in_userid] + 1
    else:
        latestSellers[in_userid] =  1
    return


def recordLatestChatter(userid, conversationid):
    global latestChatterStatus
    latestChatterStatus[userid] = {"time":datetime.datetime.now(), 'conversationid':conversationid}

def recordLatestPlayer(userid, conversationid):
    global latestPlayersStatus
    global latestOnlinePlayers
    latestPlayersStatus[userid] = {"time":datetime.datetime.now(), 'conversationid':conversationid}
    if userid in latestOnlinePlayers:
        latestOnlinePlayers.pop(latestOnlinePlayers.index(userid))
    latestOnlinePlayers = [userid] + latestOnlinePlayers

def outputIntroduction(webSocketInstance, in_conversation_id, in_userid):
    demoText = "任务 |发指令| 发贴纸\n--------------------\n买币 |  buy   | 买币才是第一生产力\n--------------------\n菠菜 |  play  | 犹豫千百回,不如一把梭\n--------------------\n红包 |  beg  | 向大鳄/大牛/大猫低头"

    sendUserText(webSocketInstance, in_conversation_id, in_userid, demoText)
    outputBattle(webSocketInstance, myConfig, in_conversation_id, in_userid, battleAssetID, battleAssetName, battleAmount)

def recordFreeBonus(in_user_id):
    hashOfUserID = hashlib.sha256(in_user_id).hexdigest()
    thisFreshMan = session.query(Freshman).filter_by(userid = hashOfUserID).first()
    if thisFreshMan != None:
        thisFreshMan.bonusCounter = thisFreshMan.bonusCounter + 1
        session.commit()
    else:
        newFreshMan = Freshman()
        newFreshMan.userid = hashOfUserID
        newFreshMan.bonusCounter = 1
        session.add(newFreshMan)
        session.commit()

def notFreshMen(in_user_id):
    hashOfUserID = hashlib.sha256(in_user_id).hexdigest()
    thisFreshMan = session.query(Freshman).filter_by(userid = hashOfUserID).first()
    if thisFreshMan != None and thisFreshMan.bonusCounter > 20:
        return True
    return False


def outputRandomeBonus(data_inMessage, in_robot, in_config, in_asset_id):
    if notFreshMen(data_inMessage['user_id']):
        sendUserText(ws, data_inMessage['conversation_id'], data_inMessage['user_id'], u"新手期已过，没有奖励了".encode("utf-8"))
        return
    recordFreeBonus(data_inMessage['user_id'])

    global freeBonusTimeTable
    now = datetime.datetime.now()
    if data_inMessage['user_id'] in freeBonusTimeTable:
        oldtime = freeBonusTimeTable[data_inMessage['user_id']]
        timediff = (now - oldtime).total_seconds()
        min_interval = 60 * 5
        if timediff < min_interval:
            btn = u"点钞机过热，还需要冷却".encode('utf-8') + str(int(min_interval - timediff)) + u"秒".encode('utf-8')
	    params = {"conversation_id": data_inMessage['conversation_id'],"recipient_id":data_inMessage['user_id'],"message_id":str(uuid.uuid4()),"category":"PLAIN_TEXT","data":base64.b64encode(btn)}
            writeMessage(ws, "CREATE_MESSAGE",params)
            return
    freeBonusTimeTable[data_inMessage['user_id']] = now
    bonus = str(random.randint(0,12345))
    transferTo(in_robot, in_config, data_inMessage['user_id'] , in_asset_id,bonus,"you are rich")

def outExchange(webSocketInstance, in_config, in_conversation_id, in_userid):
    sendUserGameEntrance(webSocketInstance, in_config, in_conversation_id, in_userid, PER_PRS.encode('utf-8') + u"PRS动态兑换".encode('utf-8') + u"吹牛币".encode('utf-8'),mixin_asset_list.PRS_ASSET_ID,  float(PER_PRS))

    sendUserPayAppButton(webSocketInstance, in_config, in_conversation_id, in_userid, PER_CNB.encode('utf-8') + u"吹牛币兑换".encode('utf-8') + u"PRS".encode('utf-8'),mixin_asset_list.CNB_ASSET_ID,  float(PER_CNB), "#ffc371", "CNB2PRS")




def welcomeToMacao(webSocketInstance, in_config, in_conversation_id, in_userid):
    outputBattle(webSocketInstance, in_config, in_conversation_id, in_userid, battleAssetID, battleAssetName, battleAmount)

    sendUserGameEntrance(webSocketInstance, in_config, in_conversation_id, in_userid, u"闪电比大小 ".encode('utf-8') + str(payAmount).encode('utf-8') + u" CANDY".encode('utf-8'),mixin_asset_list.CANDY_ASSET_ID,  payAmount , colorOfCANDY, "CANDY_Showhand")
    sendUserGameEntrance(webSocketInstance, in_config, in_conversation_id, in_userid, u"闪电比大小 ".encode('utf-8') + str(payAmountCNB).encode('utf-8') + u" CNB".encode('utf-8'),mixin_asset_list.CNB_ASSET_ID,  payAmountCNB, colorOfCNB, "CNB_Showhand")

def shouldProcessForBattle(in_user_id, in_asset_amount, in_battleAmount, in_asset_id, in_battle_asset_id):
    return str(in_asset_amount) == str(in_battleAmount)

def processForMultiUserBattle(in_websocket, in_robot, in_config, in_user_id, in_trace_id, in_snapID, in_conversion_id, in_asset_amount, in_asset_id, dbSession, asset_name = ""):
    thisUserInORM = userNameInDataBase(in_user_id)
    if thisUserInORM == None:
        sendUserAppButton(in_websocket, in_conversion_id, in_user_id, "http://dapai.one:9091", u"尊姓大名？".encode('utf-8'), colorOfLink = "#d53120")
    realLink = u"https://mixin.one/snapshots/".encode('utf-8') + in_snapID.encode('utf-8')
    realText = u"抽到".encode('utf-8') + mostLeftNumber(in_snapID).encode('utf-8') + u"，点我查看".encode('utf-8')
    sendUserAppButton(in_websocket, in_conversion_id, in_user_id, realLink, realText, colorOfLink = "#d53120")

    if isUserPayToJoinBattle(in_trace_id, dbSession):
        join_batte_id = userDidJoinBattle(in_user_id, in_trace_id, in_snapID, in_asset_id, in_asset_amount, dbSession)
        remainSeat = remainSeatInTable(join_batte_id, dbSession)
        if remainSeat == 0:
            sorted_user_with_dice = calculateBattelResult(join_batte_id, dbSession, in_robot, in_config)
            result_string = ""
            for eachUser in sorted_user_with_dice:
                result_string = result_string + userNameOrHashOrIDInDataBase(eachUser[0]).encode('utf-8') + u":".encode('utf-8') + str(eachUser[1]).encode('utf-8') + u"\n".encode('utf-8') 
            sendUserText(in_websocket, in_conversion_id, in_user_id, result_string)
            newBattleUUID = str(uuid.uuid1())
            for eachGroupConversationID in allGroupsOfRobot():
                sendGroupText(in_websocket, eachGroupConversationID, result_string)
                textForGroup = u"比赛结束，启动新一轮".encode('utf-8') + asset_name.encode('utf-8') + str(MAX_PLAYER_BATTLE).encode('utf-8') + u"人比大小".encode('utf-8')
                sendGroupGameEntrance(in_websocket, in_config, eachGroupConversationID, textForGroup,in_asset_id,  in_asset_amount, "#ff0033", "LYBattle", newBattleUUID)
            return
        else:
            toBroadCastBattleTraceId = generateTraceIDForNextChallenger(join_batte_id, dbSession)
            remainSeat = remainSeatInTable(join_batte_id, dbSession)
            text4fighter = asset_name.encode('utf-8') + u" 比大小:".encode('utf-8') + userNameOrHashOrIDInDataBase(in_user_id).encode('utf-8') + battle_alreadyText.encode('utf-8') + u",仅剩".encode('utf-8') + str(remainSeat).encode('utf-8') + u"席".encode('utf-8')
            for eachGroupConversationID in allGroupsOfRobot():
                sendGroupGameEntrance(in_websocket, in_config, eachGroupConversationID, text4fighter,in_asset_id,  in_asset_amount, "#ff0033", "LYBattle", toBroadCastBattleTraceId)
            return
    else:
        new_battle_id = userCreateBattle(in_user_id, in_trace_id, in_snapID, in_asset_id, in_asset_amount, dbSession, "BigSmall", MAX_PLAYER_BATTLE)
        toBroadCastBattleTraceId = generateTraceIDForNextChallenger(new_battle_id, dbSession)
        remainSeat = remainSeatInTable(new_battle_id, dbSession)
        for eachGroupConversationID in allGroupsOfRobot():
            text4fighter = asset_name.encode('utf-8') + u" 比大小:".encode('utf-8') + userNameOrHashOrIDInDataBase(in_user_id).encode('utf-8') + battle_alreadyText.encode('utf-8') + u",仅剩".encode('utf-8') + str(remainSeat).encode('utf-8') + u"席".encode('utf-8')
            sendGroupGameEntrance(in_websocket, in_config, eachGroupConversationID, text4fighter,in_asset_id,  in_asset_amount, "#ff0033", "LYBattle", toBroadCastBattleTraceId)
        return

def increaseWinScoreFor(in_userid):
    global latestPlayersScore
    if in_userid in latestPlayersScore:
        oldscore = latestPlayersScore[in_userid]
        latestPlayersScore[in_userid] = {"win": oldscore["win"] + 1, "lose": oldscore["lose"], "draw":oldscore["draw"]}
    else:
        latestPlayersScore[in_userid] = {"win": 1, "lose": 0, "draw":0}

def increaseLoseScoreFor(in_userid):
    global latestPlayersScore
    if in_userid in latestPlayersScore:
        oldscore = latestPlayersScore[in_userid]
        latestPlayersScore[in_userid] = {"win": oldscore["win"] , "lose": oldscore["lose"] + 1, "draw":oldscore["draw"]}
    else:
        latestPlayersScore[in_userid] = {"win": 0, "lose": 1, "draw":0}

def increaseDrawScoreFor(in_userid):
    global latestPlayersScore
    if in_userid in latestPlayersScore:
        oldscore = latestPlayersScore[in_userid]
        latestPlayersScore[in_userid] = {"win": oldscore["win"] , "lose": oldscore["lose"], "draw":oldscore["draw"] + 1}
    else:
        latestPlayersScore[in_userid] = {"win": 0, "lose": 0, "draw":1}

def winnerRankingList():
    result = []
    for eachWinner in latestPlayersScore:
        result.append((eachWinner, latestPlayersScore[eachWinner]["win"]))
    return sorted(result, key=lambda tup: tup[1], reverse = True)

def playRankingList():
    result = []
    for eachWinner in latestPlayersScore:
        result.append((eachWinner, latestPlayersScore[eachWinner]["win"] + latestPlayersScore[eachWinner]["lose"]+ latestPlayersScore[eachWinner]["draw"]))
    return sorted(result, key=lambda tup: tup[1], reverse = True)

def winRateRankingList():
    result = []
    for eachWinner in latestPlayersScore:
        result.append((eachWinner, int(100.0 * (latestPlayersScore[eachWinner]["win"])/(latestPlayersScore[eachWinner]["win"] + latestPlayersScore[eachWinner]["lose"]+ latestPlayersScore[eachWinner]["draw"]))))
    return sorted(result, key=lambda tup: tup[1], reverse = True)


def myScoreText(in_userid):

    if in_userid in latestPlayersScore:
        scoreOfUser = latestPlayersScore[in_userid]
        win_s =  scoreOfUser["win"]
        lose_s = scoreOfUser["lose"]
        draw_s = scoreOfUser["draw"]
        mytext = str(win_s).encode('utf-8') + u"胜，".encode('utf-8') + str(lose_s).encode('utf-8') + u"负，".encode('utf-8') + str(draw_s).encode('utf-8') + u"平".encode('utf-8')
        return mytext
    else:
        return u"你还没有玩过".encode('utf-8')

def processBattleFor(webSocketInstance, in_robot,in_msgid,in_config, in_conversation_id, in_userid, in_snap_id, in_asset_id, in_asset_amount):
    global groupOfFighters
    global battleWinner
    realLink = u"https://mixin.one/snapshots/".encode('utf-8') + in_snap_id.encode('utf-8')
    realText = u"抽到".encode('utf-8') + mostLeftNumber(in_snap_id).encode('utf-8') + u"，点我查看".encode('utf-8')
    sendUserAppButton(webSocketInstance, in_conversation_id, in_userid, realLink, realText, colorOfLink = "#d53120")

    recordLatestPlayer(in_userid, in_conversation_id)

    singleObj = {"userid":in_userid, "conversion_id":in_conversation_id, "snapid":in_snap_id, "snapValue":int(mostLeftNumber(in_snap_id)), "amount":float(in_asset_amount), "assetid":in_asset_id}
    groupOfFighters.append(singleObj)
    totalToNotify = len(groupOfFighters)

    now = datetime.datetime.now()
    for eachPlayerID in latestOnlinePlayers[:totalToNotify]:
        if eachPlayerID == in_userid or eachPlayerID == groupOfFighters[0]["userid"]:
            continue

        timeDiff = (now - latestPlayersStatus[eachPlayerID]["time"]).total_seconds()
        if timeDiff > 300:
            continue
        outputBattle(webSocketInstance, in_config, latestPlayersStatus[eachPlayerID]['conversationid'], eachPlayerID, battleAssetID, battleAssetName, battleAmount)
    for eachGroupConversationID in allGroupsOfRobot():
        outputBattleToGroup(webSocketInstance, in_config, eachGroupConversationID, in_userid, battleAssetID, battleAssetName, battleAmount)
    if len(groupOfFighters) > 1:
        firstFighter = groupOfFighters.pop(0)
        secondFighter= groupOfFighters.pop(0)
        if firstFighter["snapValue"] == secondFighter["snapValue"]:
            transferTo(in_robot, in_config, firstFighter["userid"] , in_asset_id ,firstFighter["amount"],"you are rich")
            transferTo(in_robot, in_config, secondFighter["userid"] , in_asset_id ,secondFighter["amount"],"you are rich")

            drawgameText0 = u"与".encode('utf-8') + userNameOrHashOrIDInDataBase(secondFighter["userid"]).encode('utf-8') + u"打平".encode('utf-8')
            drawgameText1 = u"与".encode('utf-8') + userNameOrHashOrIDInDataBase(firstFighter["userid"]).encode('utf-8') + u"打平".encode('utf-8')

            realLink0 = u"https://mixin.one/snapshots/".encode('utf-8') + secondFighter["snapid"].encode('utf-8')
            sendUserAppButton(webSocketInstance, firstFighter["conversion_id"], firstFighter["userid"] , realLink0, drawgameText0, colorOfLink = "#d53120")
            realLink1 = u"https://mixin.one/snapshots/".encode('utf-8') + firstFighter["snapid"].encode('utf-8')
            sendUserAppButton(webSocketInstance, secondFighter["conversion_id"], secondFighter["userid"] , realLink1, drawgameText1, colorOfLink = "#d53120")


            outputBattle(webSocketInstance, in_config, firstFighter["conversion_id"], firstFighter["userid"], battleAssetID, battleAssetName, battleAmount)
            outputBattle(webSocketInstance, in_config, secondFighter["conversion_id"], secondFighter["userid"], battleAssetID, battleAssetName, battleAmount)

            increaseDrawScoreFor(firstFighter["userid"])
            increaseDrawScoreFor(secondFighter["userid"])

            sendUserText(webSocketInstance, firstFighter["conversion_id"], firstFighter["userid"], myScoreText(firstFighter["userid"]))
            sendUserText(webSocketInstance, secondFighter["conversion_id"], secondFighter["userid"], myScoreText(secondFighter["userid"]))
            return
        if firstFighter["snapValue"] > secondFighter["snapValue"]:
            winner = firstFighter 
            loser = secondFighter
        else:
            winner = secondFighter
            loser = firstFighter
        winnerText = mostLeftNumber(winner["snapid"]).encode('utf-8') + u" : ".encode('utf-8') + mostLeftNumber(loser["snapid"]).encode('utf-8') + u"击败了".encode('utf-8') + userNameOrHashOrIDInDataBase(loser["userid"]).encode('utf-8') + u"，点我查看".encode('utf-8')

        winnerLink = u"https://mixin.one/snapshots/".encode('utf-8') + loser["snapid"].encode('utf-8')
        loserText = mostLeftNumber(loser["snapid"]).encode('utf-8') + u" : ".encode('utf-8') + mostLeftNumber(winner["snapid"]).encode('utf-8') + u"输给了".encode('utf-8') + userNameOrHashOrIDInDataBase(winner["userid"]).encode('utf-8') + u"，点我查看".encode('utf-8')

        loserLink  = u"https://mixin.one/snapshots/".encode('utf-8') + winner["snapid"].encode('utf-8')


        #send winner
        transferTo(in_robot, in_config, winner["userid"] , in_asset_id ,loser["amount"] * 0.95 + winner["amount"],"you are rich")
        sendUserAppButton(webSocketInstance, winner["conversion_id"], winner['userid'], winnerLink, winnerText, colorOfLink = "#ffd700")

        #send loser
        sendUserAppButton(webSocketInstance, loser["conversion_id"],  loser["userid"], loserLink, loserText, colorOfLink = "#000000")

        #send battle again
        outputBattle(webSocketInstance, in_config, winner["conversion_id"], winner["userid"], battleAssetID, battleAssetName, battleAmount)
        outputBattle(webSocketInstance, in_config, loser["conversion_id"], loser["userid"], battleAssetID, battleAssetName, battleAmount)

        #transfer to admin
        #transferTo(in_robot, in_config, in_config.admin_uuid , in_asset_id ,str(float(in_asset_amount) * 0.05),"you are rich")

        #record score
        increaseWinScoreFor(winner["userid"])
        increaseLoseScoreFor(loser["userid"])

        #show score
        sendUserText(webSocketInstance, winner["conversion_id"], winner["userid"], myScoreText(winner["userid"]))
        sendUserText(webSocketInstance, loser["conversion_id"], loser["userid"], myScoreText(loser["userid"]))


def outputMultiBattle(in_ws, in_config, in_conv_id, in_userid, in_asset_id, in_asset_name, in_asset_amount):
    openBattle = stillOpenBattleInTable(session)
    if openBattle == None or openBattle.id < 70:
        newBattleUUID = str(uuid.uuid1())
        textForGroup = u"启动新一轮".encode('utf-8') + in_asset_name.encode('utf-8') + str(MAX_PLAYER_BATTLE).encode('utf-8') + u"人比大小".encode('utf-8')

        sendUserGameEntrance(in_ws, in_config, in_conv_id, in_userid, textForGroup,in_asset_id,  in_asset_amount, "#ff0033", "LYBattle", newBattleUUID)
    else:
        remainSeat = remainSeatInTable(openBattle.battle_id, session)
        print("battle id is" + str(openBattle.id))
        toBroadCastBattleTraceId = openBattle.trace_id

        text4fighter = in_asset_name.encode('utf-8') + u"比大小进行中，仅剩".encode('utf-8') + str(remainSeat).encode('utf-8') + u"席".encode('utf-8')
        sendUserGameEntrance(in_ws, in_config, in_conv_id, in_userid, text4fighter,in_asset_id,  in_asset_amount, "#ff0033", "LYBattle", toBroadCastBattleTraceId)
    return

def outputBattle(in_ws, in_config, in_conv_id, in_userid, in_asset_id, in_asset_name, in_asset_amount):
    outputMultiBattle(in_ws, in_config, in_conv_id, in_userid, in_asset_id, in_asset_name, in_asset_amount)
    return

def outputBattleToGroup(in_ws, in_config, in_conv_id, in_userid, in_asset_id, in_asset_name, in_asset_amount):
    thisUserInORM = userNameInDataBase(in_userid)
    text4fighter = str(in_asset_amount).encode('utf-8')  + u" ".encode('utf-8')  + in_asset_name.encode('utf-8') + u"紧跟".encode('utf-8') + userNameOrHashOrIDInDataBase(groupOfFighters[len(groupOfFighters) - 1]['userid']).encode('utf-8')
    sendGroupPay(in_ws, in_config, in_conv_id, text4fighter,in_asset_id,  in_asset_amount, "#20b2aa")


def outputRanking(in_ws, in_conversation_id, in_userid):
    winnerRankingWithName = u"胜利排行榜\n".encode('utf-8')
    for eachWinner in winnerRankingList():
        eachElement = (userNameOrHashOrIDInDataBase(eachWinner[0]), eachWinner[1])
        winnerRankingWithName = winnerRankingWithName + eachElement[0].encode('utf-8') + u' '.encode('utf-8') * (40 - len(eachElement[0].encode('utf-8'))) + str(eachElement[1]).encode('utf-8') + u"\n".encode('utf-8')
    playRankingWithName = u"参战排行榜\n".encode('utf-8')
    for eachPlayer in playRankingList():
        eachElement = (userNameOrHashOrIDInDataBase(eachPlayer[0]), eachPlayer[1])
        playRankingWithName = playRankingWithName + eachElement[0].encode('utf-8') + u' '.encode('utf-8') * (40 - len(eachElement[0].encode('utf-8'))) + str(eachElement[1]).encode('utf-8') + u"\n".encode('utf-8')
    rateRankingWithName = u"胜率排行榜\n".encode('utf-8')
    for eachPlayer in winRateRankingList():
        eachElement = (userNameOrHashOrIDInDataBase(eachPlayer[0]), eachPlayer[1])
        rateRankingWithName = rateRankingWithName + eachElement[0].encode('utf-8') + u' '.encode('utf-8') * (40 - len(eachElement[0].encode('utf-8'))) + str(eachElement[1]).encode('utf-8') + u"%\n".encode('utf-8')

    sendUserText(in_ws, in_conversation_id, in_userid, winnerRankingWithName)
    sendUserText(in_ws, in_conversation_id, in_userid, playRankingWithName)
    sendUserText(in_ws, in_conversation_id, in_userid, rateRankingWithName)

def bancor_inconnector_outtoken(inconnector, remainConnector, CW, outtoken_total):
    return (pow(1 + inconnector/remainConnector, CW) - 1) * outtoken_total

def bancor_intoken_outconnector(intoken, remainConnector, CW, outtoken_total):
    return remainConnector * (pow(1.0 + intoken/outtoken_total, 1/CW) - 1)

CNB_Total = 10 * 1000 * 1000 * 1000 * 1000
CW_PRS_CNB = 0.0037

def bancor_inprs_outcnb(inPRS, remainPRSBeforePay, CW):
    return bancor_inconnector_outtoken(inPRS, remainPRSBeforePay, CW, CNB_Total)

def bancor_incnb_outprs(inCNB, remainPRS, CW):
    return bancor_intoken_outconnector(inCNB, remainPRS, CW, CNB_Total)

def on_message(ws, message):
    global bonusAssetID
    global bonusUnitText
    global payAmount
    global admin_conversation_id
    global currentFighter
    global groupOfFighters
    global freeBonusTimeTable
    global latestOnlinePlayers
    global latestPlayersScore
    global latestPlayersStatus
    global totalCNBBuyBack
    global battleAmount
    global battleAssetName
    global battleAssetID
    global battle_alreadyText
 


    inbuffer = StringIO(message)
    f = gzip.GzipFile(mode="rb", fileobj=inbuffer)
    rdata_injson = f.read()
    rdata_obj = json.loads(rdata_injson)
    action = rdata_obj["action"]

    if action not in ["ACKNOWLEDGE_MESSAGE_RECEIPT" ,"CREATE_MESSAGE", "LIST_PENDING_MESSAGES"]:
        print("unknow action")
        print(rdata_obj)
        return

    if action in ["ACKNOWLEDGE_MESSAGE_RECEIPT", "LIST_PENDING_MESSAGES"]:
        return

    if action == "CREATE_MESSAGE" and 'error' in rdata_obj:

        print(rdata_obj)
        if "data" in rdata_obj:
            msgid = rdata_obj["data"]["message_id"]
            conversationid = data["conversation_id"]
            replyMessage(ws, msgid)
        return
 
    if action == "CREATE_MESSAGE" and 'error' not in rdata_obj:
        msgid = rdata_obj["data"]["message_id"]
        data = rdata_obj["data"]
        typeindata = data["type"]
        categoryindata = data["category"]
        dataindata = data["data"]
        conversationid = data["conversation_id"]
        print(data)
        replyMessage(ws, msgid)

        if data['user_id'] == mixin_config.admin_uuid:
            admin_conversation_id = data["conversation_id"]

        if categoryindata not in ["SYSTEM_ACCOUNT_SNAPSHOT", "PLAIN_TEXT", "SYSTEM_CONVERSATION", "PLAIN_STICKER","PLAIN_IMAGE" ]:
            return

        if categoryindata == "SYSTEM_CONVERSATION":
            realData = base64.b64decode(dataindata)
            sysConversationObj = json.loads(realData)
            if sysConversationObj["action"] == "ADD":
                sendGroupText(ws, conversationid, "hello")
                addOneGroup(conversationid)

            if sysConversationObj["action"] == "REMOVE":
                removeOneGroup(conversationid)
            return
        if categoryindata == "PLAIN_IMAGE":
            realData = base64.b64decode(dataindata)


        if categoryindata == "SYSTEM_ACCOUNT_SNAPSHOT" and typeindata == "message":
            realData = base64.b64decode(dataindata)
            realAssetObj = json.loads(realData)
            print(realAssetObj)
            userid = realAssetObj["counter_user_id"]
            asset_amount = realAssetObj["amount"]

            localSnapID = realAssetObj["snapshot_id"]
 
            if realAssetObj["asset_id"] == mixin_asset_list.CNB_ASSET_ID:
                if float(asset_amount) > 0:
                    if shouldProcessForBattle(data['user_id'], asset_amount, battleAmount, realAssetObj["asset_id"], battleAssetID):
                        #processBattleFor(ws, mixin_api_robot,msgid,myConfig, data['conversation_id'], data['user_id'], realAssetObj["snapshot_id"], realAssetObj["asset_id"], asset_amount)
                        processForMultiUserBattle(ws, mixin_api_robot, myConfig, userid, realAssetObj["trace_id"], realAssetObj["snapshot_id"], conversationid, float(asset_amount), realAssetObj["asset_id"], session, battleAssetName)

                        return
                    if float(asset_amount) > (payAmountCNB  - 1) and float(asset_amount) < (payAmountCNB + 1):
                        tryLucky(ws, msgid, realAssetObj["snapshot_id"], data['conversation_id'], data['user_id'], mixin_api_robot, myConfig, realAssetObj["asset_id"], payAmountCNB * bonusAmp , payAmountCNB)
                        welcomeToMacao(ws, mixin_config, data['conversation_id'], data['user_id'])
                        recordLatestPlayer(data['user_id'], data['conversation_id'])
                        return
                    if asset_amount == PER_CNB or asset_amount == str(10 * int(PER_CNB)) or asset_amount == str(100 * int(PER_CNB)):
                        remainCNB_PRS = listCNBPRSAssets(mixin_api_robot, myConfig)
                        remainPRS = float(remainCNB_PRS["PRS"])
                        paidCNB = float(asset_amount)

                        toSendPRS = bancor_incnb_outprs(paidCNB, remainPRS, CW_PRS_CNB)
                        if toSendPRS < remainPRS:
                            print("remainCNB " + remainCNB_PRS["CNB"])
                            print("remainPRS " + remainCNB_PRS["PRS"])
                            print("paidCNB " + str(paidCNB))
                            print("toSendPRS " + str(toSendPRS))

                            if transferTo(mixin_api_robot, myConfig, userid, mixin_asset_list.PRS_ASSET_ID ,str(toSendPRS),"rich"):
                                totalCNBBuyBack = totalCNBBuyBack + 1
                                recordCNBSeller(userid)
                                sendUserGameEntrance(ws, myConfig, data['conversation_id'], userid, str(10 * float(PER_CNB)).encode('utf-8') + u"CNB兑换".encode('utf-8') + u"PRS".encode('utf-8'),mixin_asset_list.CNB_ASSET_ID,  float(PER_CNB) * 10)
                                sendUserGameEntrance(ws, myConfig, data['conversation_id'], userid, str(100 * float(PER_CNB)).encode('utf-8') + u"CNB兑换".encode('utf-8') + u"PRS".encode('utf-8'),mixin_asset_list.CNB_ASSET_ID,  float(PER_CNB) * 100)

                                return
                        else:
                            transferTo(mixin_api_robot, myConfig, userid, realAssetObj["asset_id"] ,asset_amount,"rollback")
                            sendUserText(ws, data['conversation_id'], userid, u"库存不足，请提醒老板补货".encode("utf-8"))
                            sendUserText(ws, admin_conversation_id, mixin_config.admin_uuid, u"老板，CNB库存不足".encode("utf-8"))
                            return
            if realAssetObj["asset_id"] == mixin_asset_list.PRS_ASSET_ID:
                if float(asset_amount) < 0:
                    return
                if asset_amount == PER_PRS or asset_amount == str(10 * int(PER_PRS)) or asset_amount == str(100 * int(PER_PRS)):
                    remainCNB_PRS = listCNBPRSAssets(mixin_api_robot, myConfig)
                    remainCNB = float(remainCNB_PRS["CNB"])
                    remainPRS = float(remainCNB_PRS["PRS"])
                    paidPRS = float(asset_amount)
                    remainPRSBeforePay = remainPRS - paidPRS
                    toSendCNB = bancor_inprs_outcnb(paidPRS, remainPRSBeforePay,CW_PRS_CNB)
                    if toSendCNB < remainCNB:
                        print("remainCNB " + remainCNB_PRS["CNB"])
                        print("remainPRS " + remainCNB_PRS["PRS"])
                        print("paidPRS" + str(paidPRS))
                        print("toSendCNB " + str(toSendCNB))

                        if transferTo(mixin_api_robot, myConfig, userid, mixin_asset_list.CNB_ASSET_ID,str(toSendCNB),"rich"):
                            recordCNBBuyer(userid)
                            sendUserGameEntrance(ws, myConfig, data['conversation_id'], userid, str(10 * float(PER_PRS)).encode('utf-8') + u"PRS兑换".encode('utf-8') + u"吹牛币".encode('utf-8'),mixin_asset_list.PRS_ASSET_ID,  float(PER_PRS) * 10)
                            sendUserGameEntrance(ws, myConfig, data['conversation_id'], userid, str(100 * float(PER_PRS)).encode('utf-8') + u"PRS兑换".encode('utf-8') + u"吹牛币".encode('utf-8'),mixin_asset_list.PRS_ASSET_ID,  float(PER_PRS) * 100)


                        return

                if float(asset_amount) > 1001 or float(asset_amount) < 999:
                    transferTo(mixin_api_robot, myConfig, userid, realAssetObj["asset_id"],asset_amount,"rollback")
                    sendUserText(ws, data['conversation_id'], userid, u"库存不足，请提醒老板补货".encode("utf-8"))
                    sendUserText(ws, admin_conversation_id, mixin_config.admin_uuid, u"老板，CNB库存不足".encode("utf-8"))
                    return
                return
            if realAssetObj["asset_id"] == mixin_asset_list.EOS_ASSET_ID:
                if float(asset_amount) > 0:
                    transferTo(mixin_api_robot, myConfig, userid, realAssetObj["asset_id"],asset_amount,"rollback")
                    return
                return
            if realAssetObj["asset_id"] == mixin_asset_list.SIACOIN_ASSET_ID:
                if asset_amount == PER_SIA:
                    showReceipt(ws, conversationid, userid, realAssetObj["snapshot_id"])
                    if transferTo(mixin_api_robot, myConfig, userid, mixin_asset_list.CNB_ASSET_ID,CNB_PER_PRS,"rich"):
                        recordCNBBuyer(userid)
                        return
                if float(asset_amount) > 0:
                    transferTo(mixin_api_robot, myConfig, userid, realAssetObj["asset_id"],asset_amount,"rollback")
                    sendUserText(ws, data['conversation_id'], userid, u"库存不足，请提醒老板补货".encode("utf-8"))
                    sendUserText(ws, admin_conversation_id, mixin_config.admin_uuid, u"老板，CNB库存不足".encode("utf-8"))

                    return
                return
            if realAssetObj["asset_id"] == mixin_asset_list.XIN_ASSET_ID:
                if asset_amount == PER_XIN or asset_amount == str(10 * float(PER_XIN)):
                    times = float(asset_amount)/float(PER_XIN)
                    showReceipt(ws, conversationid, userid, realAssetObj["snapshot_id"])
                    if transferTo(mixin_api_robot, myConfig, userid, mixin_asset_list.CNB_ASSET_ID,str(times * float(CNB_PER_PRS)),"rich"):
                        sendUserGameEntrance(ws, myConfig, data['conversation_id'], userid, str(10 * float(PER_XIN)).encode('utf-8') + u"XIN兑换".encode('utf-8') + str(10 * float(CNB_PER_PRS)).encode('utf-8')+ u"吹牛币".encode('utf-8'),mixin_asset_list.XIN_ASSET_ID,  float(PER_XIN) * 10)
                        recordCNBBuyer(userid)
                        return
                if float(asset_amount) > 0:
                    transferTo(mixin_api_robot, myConfig, userid, realAssetObj["asset_id"],asset_amount,"rollback")
                    sendUserText(ws, data['conversation_id'], userid, u"库存不足，请提醒老板补货".encode("utf-8"))
                    sendUserText(ws, admin_conversation_id, mixin_config.admin_uuid, u"老板，CNB库存不足".encode("utf-8"))

                    return
                return


            if realAssetObj["asset_id"] == mixin_asset_list.CANDY_ASSET_ID :
                if shouldProcessForBattle(data['user_id'], asset_amount, battleAmount, realAssetObj["asset_id"], battleAssetID):
                    processForMultiUserBattle(ws, mixin_api_robot, myConfig, userid, realAssetObj["trace_id"], realAssetObj["snapshot_id"], conversationid, float(asset_amount), realAssetObj["asset_id"], session, battleAssetName)

                    #processBattleFor(ws, mixin_api_robot,msgid,myConfig, data['conversation_id'], data['user_id'], realAssetObj["snapshot_id"], realAssetObj["asset_id"], asset_amount)
                    return
                if asset_amount == PER_CANDY:
                    tryLucky(ws, msgid, realAssetObj["snapshot_id"], data['conversation_id'], data['user_id'], mixin_api_robot, myConfig, realAssetObj["asset_id"] , payAmount * bonusAmp, payAmount)
                    recordLatestPlayer(userid, conversationid)
                    sendUserGameEntrance(ws, myConfig, data['conversation_id'], data['user_id'], u"接着梭CANDY".encode('utf-8'),mixin_asset_list.CANDY_ASSET_ID,  payAmount , colorOfCANDY)
                    sendUserGameEntrance(ws, myConfig, data['conversation_id'], data['user_id'], u"接着梭CNB".encode('utf-8'),mixin_asset_list.CNB_ASSET_ID,  payAmountCNB, colorOfCNB)
                    return
                if float(asset_amount) > 0:
                    transferTo(mixin_api_robot, myConfig, userid, realAssetObj["asset_id"],asset_amount,"rollback")
                    sendUserText(ws, data['conversation_id'], userid, u"库存不足，请提醒老板补货".encode("utf-8"))
                    sendUserText(ws, admin_conversation_id, mixin_config.admin_uuid, u"老板，CNB库存不足".encode("utf-8"))

                    return

        if categoryindata == "PLAIN_STICKER":
            ConversationId = data['conversation_id']
            realStickerData = base64.b64decode(dataindata)
            realStickerObj = json.loads(realStickerData)

            if realStickerObj['album_id'] == "eb002790-ef9b-467d-93c6-6a1d63fa2bee":
                if realStickerObj['name'] == 'productive':
                    outExchange(ws, myConfig, ConversationId, data['user_id'])
                    return
                if realStickerObj['name'] == 'cooling_off':
                    welcomeToMacao(ws, myConfig, ConversationId, data['user_id'])
                    outputRanking(ws, ConversationId, data['user_id'])
                    return
                if realStickerObj['name'] == 'no_money':
                    sendUserAppButton(ws, ConversationId, data['user_id'], "https://babelbank.io", u"数字资产抵押贷款了解一下？".encode('utf-8'))
                    return
                if realStickerObj['name'] in ['capital_predator', 'capital_cattle', 'capital_cat']:
                    outputRandomeBonus(data, mixin_api_robot, myConfig, mixin_asset_list.CNB_ASSET_ID)
                    return
            if realStickerObj['album_id'] == "36a361eb-943d-4e34-ac3e-d327d7b9be57":
                if realStickerObj['name'] == 'fuck':
                    welcomeToMacao(ws, myConfig, ConversationId, data['user_id'])
                    outputRanking(ws, ConversationId, data['user_id'])

                return

        if categoryindata == "PLAIN_TEXT" and typeindata == "message":
            if data['user_id'] in ["7921bb6f-f2e0-4ecd-a58e-e126c0437ed2", "f4456f2f-5b05-4779-9307-f037e712356b", "9478537e-6171-455f-a219-9bfb843e35d8", "f875e041-34b4-4edc-aed5-9e0188dd88da"]:
                return
            ConversationId = data['conversation_id']
            realData = base64.b64decode(dataindata)
            print(realData)
            if data['user_id'] in latestChatterStatus:
                now = datetime.datetime.now()
                timeDiff = (now - latestChatterStatus[data['user_id']]["time"]).total_seconds()
                if timeDiff < 5:
                    print("too frequent text")
                    return
                recordLatestChatter(data['user_id'], ConversationId)
            else:
                recordLatestChatter(data['user_id'], ConversationId)


            if 'gamedeposit' == realData:

                sendUserPayAppButton(ws, myConfig, ConversationId, data['user_id'], u"deposit CNB".encode('utf-8'),mixin_asset_list.CNB_ASSET_ID,  123456789012, "#ff0033")
                sendUserPayAppButton(ws, myConfig, ConversationId, data['user_id'], u"deposit CANDY".encode('utf-8'),mixin_asset_list.CANDY_ASSET_ID,  payAmount * 100, "#20b2aa")
                sendUserPayAppButton(ws, myConfig, ConversationId, data['user_id'], u"deposit prs".encode('utf-8'),mixin_asset_list.PRS_ASSET_ID,  1000, "#20b2aa")

                return
            if '?' == realData or u'？'.encode('utf-8') == realData or 'help' == realData or 'Help' == realData or u'帮助'.encode('utf-8') == realData:
                outputIntroduction(ws, ConversationId, data['user_id'])
                return
            if 'beg' == realData.lower():
                outputRandomeBonus(data, mixin_api_robot, myConfig, mixin_asset_list.CNB_ASSET_ID)
                return
            if 'b' == realData.lower() or 'prs' == realData.lower():
                outputBattle(ws, myConfig, ConversationId, data['user_id'], battleAssetID, battleAssetName, battleAmount)
                outputRanking(ws, ConversationId, data['user_id'])

                return
            if 'bc' == realData.lower() or 'candy' == realData.lower():
                outputBattle(ws, myConfig, ConversationId, data['user_id'], battleAssetID, battleAssetName, battleAmount)
                return

            if 'buy' == realData.lower():
                outExchange(ws, myConfig, ConversationId, data['user_id'])
                return
            if 'play' == realData.lower():
                welcomeToMacao(ws, myConfig, ConversationId, data['user_id'])
                return
            if 'qiong' == realData.lower():
                sendUserAppButton(ws, ConversationId, data['user_id'], "https://babelbank.io", u"数字资产抵押贷款了解一下？".encode('utf-8'))
                return
            if 'score' == realData.lower():
                sendUserText(ws, ConversationId, data['user_id'],  myScoreText(data['user_id']))
                return
            if 'cs' == realData.lower():
                outputMultiBattle(ws, myConfig, ConversationId, data['user_id'], battleAssetID, "", battleAmount)
                return
            if 'depth' == realData.lower():
                sendUserText(ws, ConversationId, data['user_id'], str(len(latestBuyers)) + " buyers")
                sendUserText(ws, ConversationId, data['user_id'], str(sorted(latestBuyers.values())) + " buyer")
                sendUserText(ws, ConversationId, data['user_id'], str(len(latestSellers)) + " seller")
                sendUserText(ws, ConversationId, data['user_id'], str(sorted(latestSellers.values())) + " seller")

            outputIntroduction(ws, ConversationId, data['user_id'])
            outExchange(ws, myConfig, ConversationId, data['user_id'])

            if data['user_id'] == mixin_config.admin_uuid:
                if 'battle' in realData:
                    sendUserText(ws, ConversationId, data['user_id'],  "bprs,bcnb, bcandy change battle")
                    return
                if 'bprs' in realData or 'bcandy' in realData or 'bcnb' in realData:
                    for eachFighter in groupOfFighters:
                        transferTo(mixin_api_robot, myConfig, eachFighter["userid"] , eachFighter["assetid"] ,eachFighter["amount"],"you are rich")
                    groupOfFighters = []

                if 'bprs' in realData:
                    battleAmount = 0.39
                    battleAssetName = u"PRS"
                    battleAssetID   = mixin_asset_list.PRS_ASSET_ID
                    return
                if 'bcandy' in realData:
                    battleAmount =  150
                    battleAssetName = u"糖果大战"
                    battleAssetID   = mixin_asset_list.CANDY_ASSET_ID
                    battle_alreadyText  = u"已包好糖果"

                    return
                if 'bcnb' in realData:
                    battleAmount =  1688168
                    battleAssetName = u"吹牛大赛"
                    battle_alreadyText  = u"已吹"

                    battleAssetID   = mixin_asset_list.CNB_ASSET_ID
                    return 

                if 'player' in realData:
                    sendUserText(ws, ConversationId, data['user_id'], str(len(latestPlayersStatus)) + "players")
                if 'txprs' in realData.lower():
                    toAnalyzeText = realData.lower()
                    endIndex = toAnalyzeText.index("txprs") + len("txprs")
                    numberOfPRS = toAnalyzeText[endIndex:]
                    transferTo(mixin_api_robot, myConfig, mixin_config.admin_uuid , mixin_asset_list.PRS_ASSET_ID,numberOfPRS,"you are rich")
                if 'txeos' in realData.lower():
                    toAnalyzeText = realData.lower()
                    endIndex = toAnalyzeText.index("txeos") + len("txeos")
                    numberOfPRS = toAnalyzeText[endIndex:]
                    transferTo(mixin_api_robot, myConfig, mixin_config.admin_uuid , mixin_asset_list.EOS_ASSET_ID,numberOfPRS,"you are rich")
                if 'txsia' in realData.lower():
                    toAnalyzeText = realData.lower()
                    endIndex = toAnalyzeText.index("txsia") + len("txsia")
                    numberOfPRS = toAnalyzeText[endIndex:]
                    transferTo(mixin_api_robot, myConfig, mixin_config.admin_uuid , mixin_asset_list.SIACOIN_ASSET_ID,numberOfPRS,"you are rich")
                if 'txcandy' in realData.lower():
                    toAnalyzeText = realData.lower()
                    endIndex = toAnalyzeText.index("txcandy") + len("txcandy")
                    numberOfPRS = toAnalyzeText[endIndex:]
                    transferTo(mixin_api_robot, myConfig, mixin_config.admin_uuid , mixin_asset_list.CANDY_ASSET_ID,numberOfPRS,"you are rich")
                if 'txxin' in realData.lower():
                    toAnalyzeText = realData.lower()
                    endIndex = toAnalyzeText.index("txxin") + len("txxin")
                    numberOfPRS = toAnalyzeText[endIndex:]
                    transferTo(mixin_api_robot, myConfig, mixin_config.admin_uuid , mixin_asset_list.XIN_ASSET_ID,numberOfPRS,"you are rich")
                if 'txcnb' in realData.lower():
                    toAnalyzeText = realData.lower()
                    endIndex = toAnalyzeText.index("txcnb") + len("txcnb")
                    numberOfPRS = toAnalyzeText[endIndex:]
                    transferTo(mixin_api_robot, myConfig, mixin_config.admin_uuid , mixin_asset_list.CNB_ASSET_ID,numberOfPRS,"you are rich")



                if 'qq2' in realData:
                    transferTo(mixin_api_robot, myConfig, mixin_config.admin_uuid , mixin_asset_list.PRS_ASSET_ID,"2","you are rich")
                if 'qq10' in realData:
                    transferTo(mixin_api_robot, myConfig, mixin_config.admin_uuid , mixin_asset_list.PRS_ASSET_ID,"10","you are rich")
                if 'ye' in realData:
                    for eachNonZeroAsset in listAssets(mixin_api_robot, myConfig):
                        sendUserText(ws, ConversationId, data['user_id'], eachNonZeroAsset[0].encode('utf-8')+ u" : ".encode('utf-8') + str(eachNonZeroAsset[1]).encode('utf-8'))
        elif categoryindata == "PLAIN_TEXT":
            print("PLAIN_TEXT but unkonw:")
            print(rdata_obj)

SocketStatus = 0
def on_error(ws, error):
    global SocketStatus
    SocketStatus = SocketStatus + 1
    print("error")
    print(error)

def on_close(ws):
    print("### closed ###")

def on_data(ws, readableString, dataType, continueFlag):
    return

def on_open(ws):


    def run(*args):
        print("run")
        Message = {"id":str(uuid.uuid1()), "action":"LIST_PENDING_MESSAGES"}
        Message_instring = json.dumps(Message)
        fgz = StringIO()
        gzip_obj = gzip.GzipFile(mode='wb', fileobj=fgz)
        gzip_obj.write(Message_instring)
        gzip_obj.close()

        ws.send(fgz.getvalue(), opcode=websocket.ABNF.OPCODE_BINARY)
        while True:
            a = 1
            time.sleep(10)
    thread.start_new_thread(run, ())


if __name__ == "__main__":

    if SocketStatus == 0:
        while True:
            encoded = mixin_api_robot.genGETJwtToken('/', "", str(uuid.uuid4()))
            websocket.enableTrace(True)
            ws = websocket.WebSocketApp("wss://blaze.mixin.one/",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close,
                              header = ["Authorization:Bearer " + encoded],
                              subprotocols = ["Mixin-Blaze-1"],
                              on_data = on_data)
            ws.on_open = on_open
            ws.run_forever()
    print("run")
