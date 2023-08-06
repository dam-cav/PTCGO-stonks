import mysql.connector

# FIX auth_plugin not working:
# pip uninstall mysql-connector
# pip3 install mysql-connector-python

def getMyDb(config):
    return mysql.connector.connect(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        database=config['database'],
        auth_plugin=config['auth_plugin'],
        port=int(config['port']),
        autocommit=True
    )