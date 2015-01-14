#!/usr/bin/python
# -*- coding: utf-8 -*-
#CELIA GARCIA FERNANDEZ

import sys
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import SocketServer
import time
import socket
import uaclient

clientes = {}


class SmallSMILHandler(ContentHandler):
    """
    Clase para obtener las etiquetas de XML
    """

    def __init__(self):
        self.diccionario = {}
        self.etiquetas = ['server', 'database', 'log']
        self.attributosD = {
            'server': ['name', 'ip', 'puerto'],
            'database': ['path', 'passwdpath'],
            'log': ['path']}

    def startElement(self, name, attrs):
        if name in self.etiquetas:
            for value in self.attributosD[name]:
                clave = name + '_' + value
                self.diccionario[clave] = attrs.get(value, "")

    def get_tags(self):
        return self.diccionario


class SIPRegisterHandler(SocketServer.DatagramRequestHandler):
    """
    SIP Server class
    """

    def handle(self):

        # Creamos un socket
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Actualizo el diccionario
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
                    ip = self.client_address[0]
                    puerto_ad = self.client_address[1]
                    log.introducir(' Received from ', line, ip, puerto_ad)
                    # Envio 200OK
                    envio = 'SIP/2.0 200 OK\r\n\r\n'
                    print 'Enviando: ' + envio
                    self.wfile.write(envio)
                    log.introducir(' Sent to ', envio, ip, puerto_ad)
                    # Entra cliente
                    clientes[direccion] = [(ip, puerto), caducidad]
                    self.register2file(clientes)
                    # Se da de baja cliente
                    if expires == 0:
                        del clientes[direccion]
                        self.register2file(clientes)

            # INVITE
                elif metodo == 'INVITE':
                    # Ver si el destinatario está registrado
                    direccion = troceo[1].split(':')[1]
                    mi_ip = self.client_address[0]
                    mi_puerto = self.client_address[1]
                    log.introducir(' Received from ', line, mi_ip, mi_puerto)
                    aux = False
                    for cliente in clientes:
                        if cliente == direccion:
                            aux = True
                            ips = clientes[cliente][0][0]
                            ps = clientes[cliente][0][1]
                            # Reenvio invite a ua2
                            self.my_socket.connect((ips, int(ps)))
                            self.my_socket.send(line)
                            log.introducir(' Sent to ', line, ips, ps)
                            print 'Reenviando INVITE a ' + direccion
                            data = self.my_socket.recv(1024)
                            print 'Recibido -- ', data
                            log.introducir(' Received from ', data, ips, ps)
                            # Reenvio lo que recibo a ua1
                            self.wfile.write(data)
                            print 'Reenviando: ' + data
                            log.introducir(' Sent to ', data, mi_ip, mi_puerto)

                    if aux is False:
                        # Envio 404
                        Sip = 'SIP/2.0 '
                        envio = Sip + '404 User Not Found'
                        print 'Enviando: ' + envio
                        self.wfile.write(envio)
                        log.introducir(' Sent to ', envio, mi_ip, mi_puerto)

            # ACK
                elif metodo == 'ACK':
                    direccion = troceo[1].split(':')[1]
                    mi_ip = self.client_address[0]
                    mi_puerto = self.client_address[1]
                    log.introducir(' Received from ', line, mi_ip, mi_puerto)
                    for cliente in clientes:
                        if cliente == direccion:
                            uas_ip = clientes[cliente][0][0]
                            uas_p = clientes[cliente][0][1]
                            # Reenvio el ACK
                            self.my_socket.connect((uas_ip, int(uas_p)))
                            self.my_socket.send(line)
                            print 'Reenviando ACK a ' + direccion
                            log.introducir(' Sent to ', line, uas_ip, uas_p)

            # BYE
                elif metodo == 'BYE':
                    direccion = troceo[1].split(':')[1]
                    mi_ip = self.client_address[0]
                    mi_puerto = self.client_address[1]
                    log.introducir(' Received from ', line, mi_ip, mi_puerto)
                    for cliente in clientes:
                        if cliente == direccion:
                            ips = clientes[cliente][0][0]
                            ps = clientes[cliente][0][1]
                            # Reenvio el ACK
                            self.my_socket.connect((ips, int(ps)))
                            self.my_socket.send(line)
                            log.introducir(' Sent to ', line, ips, ps)
                            print 'Reenviando BYE a ' + direccion
                            data = self.my_socket.recv(1024)
                            print 'Recibido -- ', data
                            log.introducir(' Received from ', data, ips, ps)
                            # Reenvio lo que recibo a ua1
                            self.wfile.write(data)
                            print 'Reenviando: ' + data
                            log.introducir(' Sent to ', data, mi_ip, mi_puerto)

                else:
                    # Envio 405
                    mi_ip = self.client_address[0]
                    mi_puerto = self.client_address[1]
                    Sip = 'SIP/2.0 '
                    envio = Sip + '405 Method Not Allowed'
                    print 'Enviando: ' + envio
                    self.wfile.write(envio)
                    log.introducir(' Sent to ', envio, mi_ip, mi_puerto)
            else:
                break

    def register2file(self, clientes):
        """
        Vuelca el diccionario en el fichero registered.txt
        """

        fich = open(dicc['database_path'], 'w')
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

    # Creamos log
    log_fich = dicc['log_path']
    log = uaclient.LogClass(log_fich)
    log.introducir(' Starting...', '', '', '')

    # Creamos servidor register SIP y escuchamos
    ser_port = dicc['server_puerto']
    serv = SocketServer.UDPServer(("", int(ser_port)), SIPRegisterHandler)
    frase = 'Server MiServidorBigBang listening at port '
    frase += dicc['server_puerto'] + '...\r\n'
    print frase
    serv.serve_forever()
