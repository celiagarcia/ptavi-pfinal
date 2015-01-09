#!/usr/bin/python
# -*- coding: utf-8 -*-
#CELIA GARCIA FERNANDEZ

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import sys
import socket
import os
import time

class SmallSMILHandler(ContentHandler):

    def __init__(self):
        self.diccionario = {}
        self.etiquetas = ['account','uaserver', 'rtpaudio','regproxy', 'log', 'audio']
        self.attributosD = {
            'account': ['username', 'passwd'],
            'uaserver': ['ip', 'puerto'],
            'rtpaudio': ['puerto'],
            'regproxy': ['ip', 'puerto'],
            'log': ['path'],
            'audio': ['path']
            }   
    def startElement(self, name, attrs):
        if name in self.etiquetas:
            for value in self.attributosD[name]:
                clave = name + '_' + value
                self.diccionario[clave] = attrs.get(value, "")           
    def get_tags(self):
        return self.diccionario

if __name__ == "__main__":
    
    # PARAMETROS SHELL
    try:
        FICH = sys.argv[1]
        METODO = sys.argv[2].upper()
        if METODO == 'REGISTER':
            OPTION = int(sys.argv[3])
        elif METODO == 'INVITE' or 'BYE':
            OPTION = str(sys.argv[3])
        if len(sys.argv) > 4 or len(sys.argv) < 3:
            print 'Usage: python uaclient.py config method option'
            raise SystemExit
    except ValueError:
        sys.exit('Usage: python uaclient.py config method option')
    except IndexError:
        sys.exit('Usage: python uaclient.py config method option')
            
    # PARSEAR 
    parser = make_parser()
    small = SmallSMILHandler()
    parser.setContentHandler(small)
    try:
        parser.parse(open(FICH))
    except IOError:
        sys.exit('Usage: python uaclient.py config method option')
    dicc = small.get_tags()
    
    fich_log = open(dicc['log_path'], 'a')
         
        
# REGISTER
    if METODO == 'REGISTER':
        username = dicc['account_username']
        port = dicc['uaserver_puerto']
        linea = METODO + ' sip:' + username + ':' + port + ' SIP/2.0\r\n\r\n'
        linea += 'Expires: ' + str(OPTION) + '\r\n\r\n'
        
        try:
            # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
            my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect((dicc['regproxy_ip'], int(dicc['regproxy_puerto'])))
            
            print "Enviando: " + linea
            my_socket.send(linea + '\r\n')
            
            data = my_socket.recv(1024)
            print 'Recibido -- ', data
            
            print "Terminando socket..."
            my_socket.close()
            print "Fin."
            
        except socket.gaierror:
            com = 'Error: No server listening at '
            sys.exit(com + dicc['regproxy_ip'] + ' port ' + dicc['regproxy_puerto'])
        except socket.error:
            com = 'Error: No server listening at '
            sys.exit(com + dicc['regproxy_ip'] + ' port ' + dicc['regproxy_puerto'])
                
# INVITE
    elif METODO == 'INVITE':    
        linea = METODO + ' sip:' + OPTION + ' SIP/2.0\r\n'
        linea += 'Content-Type: application/sdp' + '\r\n\r\n'
        linea += 'v=0\r\n'
        linea += 'o=' + dicc['account_username'] + ' ' + dicc['uaserver_ip'] + '\r\n'
        linea += 's=ptavi-pfinal\r\n'
        linea += 't=0\r\n'
        linea += 'm=audio ' + dicc['rtpaudio_puerto'] + ' RTP\r\n\r\n'
        
        try:
            # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
            my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect((dicc['regproxy_ip'], int(dicc['regproxy_puerto'])))
            
            print "Enviando: " + linea
            my_socket.send(linea + '\r\n')
            
            data = my_socket.recv(1024)
            print 'Recibido -- ', data
            
# ACK
            datos = data.split()
            if datos[1] == '100' and datos[4] == '180' and datos[7] == '200':
                line = 'ACK sip:' + OPTION + ' SIP/2.0'
                print "Enviando: " + line + '\r\n'
                my_socket.send(line + '\r\n')                
                
            # RTP
                os.system("chmod 777 mp32rtp")
                receptor_IP = datos[13]
                receptor_Puerto = datos[17]
                fichero_audio = dicc['audio_path']
                aEjecutar = './mp32rtp -i ' + receptor_IP + ' -p '
                aEjecutar += receptor_Puerto + ' < ' + fichero_audio
                print 'Vamos a ejecutar ' + aEjecutar + '\r\n'
                os.system(aEjecutar)
                print 'Finaliza RTP' + '\r\n'

            print "Terminando socket..."
            my_socket.close()
            print "Fin."
            
        except socket.gaierror:
            com = 'Error: No server listening at '
            sys.exit(com + dicc['regproxy_ip'] + ' port ' + dicc['regproxy_puerto'])
        except socket.error:
            com = 'Error: No server listening at '
            sys.exit(com + dicc['regproxy_ip'] + ' port ' + dicc['regproxy_puerto'])
            
# BYE            
    elif METODO == 'BYE':
        linea = METODO + ' sip:' + OPTION + ' SIP/2.0\r\n'
    
        try:
            # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
            my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect((dicc['regproxy_ip'], int(dicc['regproxy_puerto'])))
            
            print "Enviando: " + linea
            my_socket.send(linea + '\r\n')
            
            data = my_socket.recv(1024)
            print 'Recibido -- ', data
            
            if data == 'SIP/2.0 200 OK':
                print "Terminando socket..."
                my_socket.close()
                print "Fin."
            
        except socket.gaierror:
            com = 'Error: No server listening at '
            sys.exit(com + dicc['regproxy_ip'] + ' port ' + dicc['regproxy_puerto'])
        except socket.error:
            com = 'Error: No server listening at '
            sys.exit(com + dicc['regproxy_ip'] + ' port ' + dicc['regproxy_puerto'])
    
    
    
    
    
    
