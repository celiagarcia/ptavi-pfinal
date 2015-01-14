#!/usr/bin/python
# -*- coding: utf-8 -*-
#CELIA GARCIA FERNANDEZ

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import sys
import SocketServer
import time
import os
import uaclient

info_rtp = {}


class XMLHandler(ContentHandler):
    """
    CLase de lectura de un fichero de configuración XML
    """
    def __init__(self):
        self.diccionario = {}
        self.etiquetas = [
            'account', 'uaserver', 'rtpaudio', 'regproxy', 'log', 'audio']
        self.attributosD = {
            'account': ['username', 'passwd'],
            'uaserver': ['ip', 'puerto'],
            'rtpaudio': ['puerto'],
            'regproxy': ['ip', 'puerto'],
            'log': ['path'],
            'audio': ['path']}

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
            pr_ip = dicc['regproxy_ip']
            pr_port = dicc['regproxy_puerto']
            if line != "":
                print "El proxy_registrar nos manda " + line
                troceo = line.split()
                metodo = troceo[0]
                log.introducir(' Received from ', line, pr_ip, pr_port)

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
                    envio += 'o=' + dicc['account_username'] + ' '
                    envio += dicc['uaserver_ip'] + '\r\n'
                    envio += 's=ptavi-pfinal\r\n'
                    envio += 't=0\r\n'
                    envio += 'm=audio ' + dicc['rtpaudio_puerto']
                    envio += ' RTP\r\n\r\n'

                    print 'Enviando: ' + envio
                    self.wfile.write(envio)
                    log.introducir(' Sent to ', envio, pr_ip, pr_port)

             # ACK
                elif metodo == 'ACK':

                    # Comienzo RTP
                    os.system("chmod 777 mp32rtp")
                    fichero_audio = dicc['audio_path']
                    aEjecutar = './mp32rtp -i ' + info_rtp['receptor_IP']
                    aEjecutar += ' -p ' + info_rtp['receptor_Puerto']
                    aEjecutar += ' < ' + fichero_audio
                    print 'Vamos a ejecutar ' + aEjecutar + '\r\n'
                    os.system(aEjecutar)
                    log.introducir(' Envio RTP', '', '', '')
                    print 'Finaliza RTP' + '\r\n'

            # BYE
                elif metodo == 'BYE':
                    # Envio 200 OK
                    envio = 'SIP/2.0 200 OK'
                    print 'Enviando: ' + envio
                    self.wfile.write(envio)
                    log.introducir(' Sent to ', envio, pr_ip, pr_port)
                    log.introducir(' Finishing.', '', '', '')

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
    small = XMLHandler()
    parser.setContentHandler(small)
    try:
        parser.parse(open(FICH))
    except IOError:
        sys.exit('Usage: python uaserver.py config')
    dicc = small.get_tags()

    # Abrimos log
    log_fich = dicc['log_path']
    log = uaclient.LogClass(log_fich)

    # Creamos servidor y escuchamos
    uas_port = dicc['uaserver_puerto']
    serv = SocketServer.UDPServer(("", int(uas_port)), SIPRegisterHandler)
    print 'Listening...\r\n'
    serv.serve_forever()
