#!/usr/bin/python
# -*- coding: utf-8 -*-
#CELIA GARCIA FERNANDEZ

import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import SocketServer
import time
import socket

clientes = {}

class SmallSMILHandler(ContentHandler):

    def __init__(self):
        self.diccionario = {}
        self.etiquetas = ['server','database', 'log']
        self.attributosD = {
            'server': ['name', 'ip', 'puerto'],
            'database': ['path', 'passwdpath'],
            'log': ['path']
            }        
    def startElement(self, name, attrs):
        if name in self.etiquetas:
            for value in self.attributosD[name]:
                clave = name + '_' + value
                self.diccionario[clave] = attrs.get(value, "")        
    def get_tags(self):
        return self.diccionario
        
class SIPRegisterHandler(SocketServer.DatagramRequestHandler):

    def handle(self):
    
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
        #Actualizo el diccionario
        for cliente in clientes.keys():
            caducidad = int(clientes[cliente][1])
            if caducidad <= time.time():
                del clientes[cliente]
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            if line != "":
                print "El cliente nos manda " + line
                troceo = line.split()
                metodo = troceo[0]
                
            # REGISTER
                if metodo == 'REGISTER':
                    direccion = troceo[1].split(':')[1]
                    puerto = troceo[1].split(':')[2]
                    expires = int(troceo[4])
                    caducidad = time.time() + expires
                    print 'Enviando: SIP/2.0 200 OK\r\n\r\n'
                    self.wfile.write('SIP/2.0 200 OK\r\n\r\n')
                    #Entra cliente
                    ip = self.client_address[0]
                    clientes[direccion] = [(ip,puerto), caducidad]
                    self.register2file(clientes)
                    #Se da de baja cliente
                    if expires == 0:
                        del clientes[direccion]
                        self.register2file(clientes)
                        
            # INVITE
                elif metodo == 'INVITE':
                    #Ver si el destinatario está registrado
                    direccion = troceo[1].split(':')[1]
                    aux = False
                    for cliente in clientes:
                        if cliente == direccion:
                            aux = True
                            uaserver_ip = clientes[cliente][0][0]
                            uaserver_puerto = clientes[cliente][0][1]
                            #reenvio invite a ua2
                            self.my_socket.connect((uaserver_ip, int(uaserver_puerto)))
                            self.my_socket.send(line)
                            print 'Reenviando INVITE a ' + direccion
                            data = self.my_socket.recv(1024)
                            print 'Recibido -- ', data
                            #reenvio lo que recibo a ua1
                            self.wfile.write(data)
                            print 'Reenviando: ' + data
                            
                           
                    if aux == False:
                        #devuelvo 404
                        Sip = 'SIP/2.0 '
                        envio = Sip + '404 User Not Found'
                        print 'Enviando: ' + envio
                        self.wfile.write(envio)  
            else:
                break
                
    def register2file(self, clientes):
        """
        Vuelca el diccionario en el fichero registered.txt
        """
        fich = open('registered.txt', 'w')
        fich.write('User\tIP\tPort\tExpires\r\n')
        for cliente in clientes:
            localhost = clientes[cliente][0][0]
            port = str(clientes[cliente][0][1])
            caduc = int(clientes[cliente][1])
            cadena = cliente + '\t' + localhost + '\t' + port + '\t'
            cadena += time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(caduc))
            cadena += '\r\n'
            fich.write(cadena)

if __name__ == "__main__":

    # PARAMETROS SHELL
    try:
        FICH = sys.argv[1]
    except ValueError:
        sys.exit('Usage: python proxy_registrar.py config')
    except IndexError:
        sys.exit('Usage: python proxy_registrar.py config')
        
    # PARSEAR 
    parser = make_parser()
    small = SmallSMILHandler()
    parser.setContentHandler(small)
    try:
        parser.parse(open(FICH))
    except IOError:
        sys.exit('Usage: python uaclient.py config method option')
    dicc = small.get_tags()
        
    # Creamos servidor register SIP y escuchamos
    serv = SocketServer.UDPServer(("", int(dicc['server_puerto'])), SIPRegisterHandler)
    print 'Server MiServidorBigBang listening at port ' + dicc['server_puerto'] + '...\r\n'
    serv.serve_forever()
