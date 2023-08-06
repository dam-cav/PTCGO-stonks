# this require you to have properly configured hosts file
import ssl
import socket

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
serverSocket.bind(("127.0.0.1",39389));
serverSocket.listen();
prot = ssl.PROTOCOL_TLS

print("waiting...")
while(True):

    (clientConnected, clientAddress) = serverSocket.accept();

    connstream = ssl.wrap_socket(clientConnected,
								server_side=True,
								certfile="certs/server.pem",
								keyfile="certs/server.key",
								ssl_version=prot) 

    print("Accepted a connection request from %s:%s"%(clientAddress[0], clientAddress[1]));

    dataFromClient = connstream.recv(1024)
    print(dataFromClient.decode());

    connstream.send("\x00\x00\x00x\x00\x00\x00\x00\x00\x00\x00\x00{\"name\":\"ConnectionService\",\"value\":{\"connectionEndPoint\":\"localhost-connection-99-9.direwolfdigital.com:8181\"}}".encode());


    dataFromClient = connstream.recv(112)
    print(dataFromClient.decode());
