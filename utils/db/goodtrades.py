import mysql.connector
from .connection import *

def getGoodTrades(config, current_table, packet_archetypeid):
    mydb = getMyDb(config)

    sql = """
    SELECT
        GivenTrades.uid As uid1,
        GivenTrades.duid As duid1,
        AskedTrades.uid As uid2,
        AskedTrades.duid AS duid2,
        CurrentValues.Value - GivenTrades.requested_quantity As gain,
        GivenTrades.requested_quantity AS risk,
        (CASE WHEN GivenTrades.extra_objects <> 0 THEN 'yes' ELSE 'no' END) AS bonus1,
        (CASE WHEN AskedTrades.extra_objects <> 0 THEN 'yes' ELSE 'no' END) AS bonus2
    FROM {} AS GivenTrades INNER JOIN {} AS AskedTrades
        ON GivenTrades.given_archetypeid = AskedTrades.requested_archetypeid

        LEFT JOIN Objects AS OggettoIntermedio
        ON GivenTrades.given_archetypeid = OggettoIntermedio.uid

        INNER JOIN (
            SELECT Trades.requested_archetypeid AS cardId, FLOOR(MAX(Trades.given_quantity/Trades.requested_quantity)) AS Value # Objects.name
            FROM Objects INNER JOIN {} AS Trades
                ON Objects.uid = Trades.requested_archetypeid
            WHERE Trades.given_archetypeid = %s
            GROUP BY Trades.requested_archetypeid
            HAVING Value > 1
        ) CurrentValues
        ON AskedTrades.given_archetypeid = CurrentValues.cardId

    WHERE GivenTrades.given_quantity >= AskedTrades.requested_quantity
        AND
        OggettoIntermedio.uid <> %s
        AND
        GivenTrades.requested_archetypeid = %s
        AND
        (
            GivenTrades.requested_quantity < CurrentValues.Value
            OR
            (
                GivenTrades.requested_quantity = CurrentValues.Value
                AND GivenTrades.extra_objects = TRUE
                AND AskedTrades.extra_objects = TRUE
            )
        )
        AND GivenTrades.owner_name != AskedTrades.owner_name

    ORDER BY gain DESC, risk ASC, bonus1 DESC, bonus2 DESC, GivenTrades.expiration_timestamp DESC
    """.format(current_table, current_table, current_table)

    mycursor = mydb.cursor(buffered=True)

    val = (packet_archetypeid, packet_archetypeid, packet_archetypeid)
    mycursor.execute(sql, val)

    result = []
    for row in mycursor:
        result.append({'uid1': row[0], 'duid1': row[1], 'uid2': row[2], 'duid2': row[3], 'gain': row[4], 'risk': row[5], 'bonus1': row[6], 'bonus2': row[7]})
    return result

def readTrade(config, current_table, duid):
    mydb = getMyDb(config)

    sql = """
    SELECT Trades.uid, Trades.creation_timestamp, Trades.expiration_timestamp, Trades.inspected_at,
    UserGives.name, UserGives.uid, UserGives.set_tag, UserGives.card_number, UserGives.mask, UserGives.foilness, UserGives.full_art, Trades.given_quantity,    Trades.extra_objects,
    UserAsks.name,  UserAsks.uid,  UserAsks.set_tag,  UserAsks.card_number,  UserAsks.mask,  UserAsks.foilness,  UserAsks.full_art,  Trades.requested_quantity
    FROM {} AS Trades
    LEFT JOIN Objects AS UserGives 
    ON Trades.given_archetypeid = UserGives.uid
    LEFT JOIN Objects AS UserAsks
    ON Trades.requested_archetypeid = UserAsks.uid
    WHERE Trades.duid = %s
    """.format(current_table)

    mycursor = mydb.cursor(buffered=True)

    val = ( duid,)
    mycursor.execute(sql, val)

    for row in mycursor:
        return {
            'uid':        row[0],
            'creation':   row[1],
            'expiration': row[2],
            'inspection': row[3],
            'given': {
                'card_name':     row[4],
                'archetype_id':  row[5],
                'set_tag':       row[6],
                'card_number':   row[7],
                'mask':          row[8],
                'foilness':      row[9],
                'full_art':      True if row[10] == 1 else False,
                'quantity':      row[11],
                'extra_objects': True if row[12] == 1 else False,
            },
            'requested': {
                'card_name':     row[13],
                'archetype_id':  row[14],
                'set_tag':       row[15],
                'card_number':   row[16],
                'mask':          row[17],
                'foilness':      row[18],
                'full_art':      True if row[19] == 1 else False,
                'quantity':      row[20],
                'extra_objects': False
            }
        }
    


def objectToPacks(config, current_table, archetype_id, packet_archetypeid):
    mydb = getMyDb(config)

    print(archetype_id)

    sql = """
    SELECT Trades.uid, Trades.creation_timestamp, Trades.expiration_timestamp, Trades.inspected_at,
    UserGives.name, UserGives.uid, UserGives.set_tag, UserGives.card_number, UserGives.mask, UserGives.foilness, UserGives.full_art, Trades.given_quantity, Trades.extra_objects,
    UserWants.name, UserWants.uid, UserWants.set_tag, UserWants.card_number, UserWants.mask, UserWants.foilness, UserWants.full_art, Trades.requested_quantity
    FROM {} AS Trades
    LEFT JOIN Objects AS UserGives 
    ON Trades.given_archetypeid = UserGives.uid
    LEFT JOIN Objects AS UserWants
    ON Trades.requested_archetypeid = UserWants.uid
    WHERE Trades.given_archetypeid = %s AND Trades.requested_archetypeid = %s
    ORDER BY requested_quantity ASC, given_quantity DESC, extra_objects DESC
    LIMIT 10
    """.format(current_table)

    # add 'AND Trades.requested_quantity = 1' in WHERE if you don't want to have to pay attention to quantity

    mycursor = mydb.cursor(buffered=True)

    val = (packet_archetypeid, archetype_id)

    mycursor.execute(sql, val)

    result = []
    for row in mycursor:
        result.append({
            'uid':        row[0],
            'creation':   row[1],
            'expiration': row[2],
            'inspection': row[3],
            'given': {
                'card_name':     row[4],
                'archetype_id':  row[5],
                'set_tag':       row[6],
                'card_number':   row[7],
                'mask':          row[8],
                'foilness':      row[9],
                'full_art':      True if row[10] == 1 else False,
                'quantity':      row[11],
                'extra_objects': True if row[12] == 1 else False,
            },
            'requested': {
                'card_name':     row[13],
                'archetype_id':  row[14],
                'set_tag':       row[15],
                'card_number':   row[16],
                'mask':          row[17],
                'foilness':      row[18],
                'full_art':      True if row[19] == 1 else False,
                'quantity':      row[20],
                'extra_objects': False
            }
        })
    return result