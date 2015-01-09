#!/usr/bin/python
# -*- coding: utf-8 -*-
#CELIA GARCIA FERNANDEZ

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import sys
import SocketServer
import time
import os

info_rtp = {}

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
        
        
class SIPRegisterHandler(SocketServer.DatagramRequestHandler):

    def handle(self):
    
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            if line != "":
                print "El proxy_registrar nos manda " + line
                troceo = line.split()
                metodo = troceo[0]

            # INVITE
                if metodo == 'INVITE':
                    info_rtp['receptor_IP'] = troceo[7]
                    info_rtp['receptor_Puerto'] = troceo[11]
                    # Envio 100, 180, 200
                    Sip = 'SIP/2.0 '
                    envio = Sip + '100 TRYING' + '\r\n\r\n'
                    envio += Sip + '180 RINGING' + '\r\n\r\n'
                    envio += Sip + '200 OK' + '\r\n'
                    envio += 'Content-Type: application/sdp\r\n\r\n'
                    envio += 'v=0\r\n'
                    envio += 'o=' + dicc['account_username'] + ' ' + dicc['uaserver_ip'] + '\r\n'
                    envio += 's=ptavi-pfinal\r\n'
                    envio += 't=0\r\n'
                    envio += 'm=audio ' + dicc['rtpaudio_puerto'] + ' RTP\r\n\r\n'

                    print 'Enviando: ' + envio
                    self.wfile.write(envio)
                    
             # ACK       
                elif metodo == 'ACK':
                
                    # Comienzo RTP
                    os.system("chmod 777 mp32rtp")
                    fichero_audio = dicc['audio_path']
                    aEjecutar = './mp32rtp -i ' + info_rtp['receptor_IP'] + ' -p '
                    aEjecutar += info_rtp['receptor_Puerto'] + ' < ' + fichero_audio
                    print 'Vamos a ejecutar ' + aEjecutar + '\r\n'
                    os.system(aEjecutar)
                    print 'Finaliza RTP' + '\r\n'
                    
            # BYE
                elif metodo == 'BYE':
                    # Envio 200 OK
                    envio = 'SIP/2.0 200 OK'
                    print 'Enviando: ' + envio
                    self.wfile.write(envio)
            else:
                break
                


if __name__ == "__main__":
  
    # PARAMETROS SHELL
    try:
        FICH = sys.argv[1]
        if len(sys.argv) > 2 or len(sys.argv) < 1:
            print 'Usage: python uaserver.py config'
            raise SystemExit
    except ValueError:
        sys.exit('Usage: python uaserver.py config')
    except IndexError:
        sys.exit('Usage: python uaserver.py config')
        
    # PARSEAR 
    parser = make_parser()
    small = SmallSMILHandler()
    parser.setContentHandler(small)
    try:
        parser.parse(open(FICH))
    except IOError:
        sys.exit('Usage: python uaserver.py config')
    dicc = small.get_tags()
    
    fich_log = open(dicc['log_path'], 'a')
    
    # Creamos servidor y escuchamos
    serv = SocketServer.UDPServer(("", int(dicc['uaserver_puerto'])), SIPRegisterHandler)
    print 'Listening...\r\n'
    serv.serve_forever()
    
    
    
