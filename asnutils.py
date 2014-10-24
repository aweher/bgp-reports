#! /usr/bin/env python

# This file is part of bgp-reports.
#
#    bgp-reports is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation version 2 of the License.
#
#    bgp-reports is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with bgp-reports.  If not, see <http://www.gnu.org/licenses/>.

__author__="Ariel Weher y Matias Comba"
__date__ ="$Sep 1, 2014 7:39:33 AM$"

import json
import os
import urllib2
import csv
import re
import time
from StringIO import StringIO
import gzip
#import HTML

def colorprint(color,txt):
    colores={
        'default':'',
        'amarillo': '\x1b[01;33m',
        'azul': '\x1b[01;34m',
        'cian': '\x1b[01;36m',
        'verde': '\x1b[01;32m',
        'rojo': '\x1b[01;31m'
    }
    print colores[color]+txt+'\x1b[00m'

def generar_reporte_global(CONFIG,force=False):
    """ Genera reportes de todos los ASN y links de la tabla mundial"""
    if (force == False):
        generar = False
    else:
        generar = True
# Veo si existen los archivos preprocesados y los leo
    if (os.path.isfile(CONFIG['tmp_dir']+"RPT_ASNsGlobal") and os.path.isfile(CONFIG['tmp_dir']+"RPT_LinksGlobal")):
        if ((os.stat(CONFIG['tmp_dir']+"RPT_ASNsGlobal").st_size > 0) and (os.stat(CONFIG['tmp_dir']+"RPT_LinksGlobal").st_size > 0)):
            f=open(CONFIG['tmp_dir']+"RPT_ASNsGlobal",'r')
            ASNsGlobales=eval(f.readline())
            f=open(CONFIG['tmp_dir']+"RPT_LinksGlobal",'r')
            LinksGlobales=eval(f.readline())
        else:
            generar = True
    else:
        generar = True
            
    if (generar==True):
        [ASNsGlobales,LinksGlobales]=make_asn_links(CONFIG['feed_dir']+CONFIG['tabla_mundial'])
        try:
            with open(CONFIG['tmp_dir']+"RPT_ASNsGlobal",'w') as f:
                f.write(repr(ASNsGlobales))
            with open(CONFIG['tmp_dir']+"RPT_LinksGlobal",'w') as f:
                f.write(repr(LinksGlobales))
        except IOError as e:
            print('Error en el archivo: '+str(e))
    
    print("\nReporte de la tabla mundial")
    print ("Cantidad de ASN's en el archivo "+CONFIG['tabla_mundial']+":"+str(len(ASNsGlobales)))
    print ("Cantidad de Links en el archivo "+CONFIG['tabla_mundial']+":"+str(len(LinksGlobales)))
    return 
    
def generar_reporte_pais(CONFIG,PAIS):    
    """De la lista Global de Links genera: ASNs de borde, Upstream de cada AS, Links dentro de un pais """
    f=open(CONFIG['tmp_dir']+"RPT_ASNsGlobal",'r')
    ASNsGlobales=eval(f.readline())
    f=open(CONFIG['tmp_dir']+"RPT_LinksGlobal",'r')
    LinksGlobales=eval(f.readline())
    
    Upstream={"":[]}
    ASNs_BORDER=list()
    Links_Pais=list()
    
    [DicRIR,DicAS]=make_asn_pais(str(CONFIG['feed_dir']+'delegated-'+find_rir_by_country(CONFIG,PAIS).lower()+'-latest'))
    
    for links in LinksGlobales:
        as0,sp,as1=links.partition(",")
        if as1 in Upstream:
            Upstream[as1]|={as0}
        else:
            Upstream[as1]={as0}
#TODO Algunos ASNs aparecen como upstreams de si mismo (11815)
            
        if ((as0 in DicRIR[PAIS]) or (as1 in DicRIR[PAIS])):
            ASNs_BORDER+=[as0,as1]            
            Links_Pais+=[links]
    
    try:
        with open(CONFIG['tmp_dir']+"RPT_ASNs_"+PAIS+"_BORDER","w") as f:
            f.write(repr(ASNs_BORDER)) #TODO Actualmente se graba pero no se usa, mejorar y armar como se graban los links
        with open(CONFIG['tmp_dir']+"RPT_Links_bgp-ixp-"+PAIS,"w") as f:
            f.write(repr(Links_Pais))
        with open(CONFIG['tmp_dir']+'RPT_Upstreams_'+PAIS,'w') as f:
            f.write(repr(Upstream))
    except IOError as e:
        print('Error en el archivo: '+str(e))
    
    PaisGL = DicRIR[PAIS] & ASNsGlobales
    
    print ("Cantidad de ASNs de "+PAIS+" en el archivo "+CONFIG['tabla_mundial']+": "+str(len(PaisGL)))
    try:
        with open(CONFIG['tmp_dir']+"RPT_ASNs_"+PAIS+"_"+CONFIG['tabla_mundial'],'w') as f:
            f.write(repr(PaisGL))
    except IOError as e:
        print('Error en el archivo: '+str(e))
    
def download(url,file,mode='w'):
    """ Descarga un archivo y lo guarda en un path """
    opener = urllib2.build_opener()
    try:
        request = urllib2.Request(url)
        request.add_header('Accept-encoding', 'gzip')
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        print e.code
        print e.read() 
    else:
        # TODO Mejorar eso con el esquema de try -> with open
        w=open(file,mode)

    try:
        ### TODO NEEDS FIX
        if response.info().get('Content-Encoding') == 'gzip':
#            print('Usando GZIP para '+file)
            buf = StringIO( response.read())
            f = gzip.GzipFile(fileobj=buf)
            data = f.read().rstrip()
        else:
            data = response.read()
        w.write(data)
        w.close()
    except OSError as e:
        print(e)
        response.close()
    except:
        print('Error: ',str(e))
        pass

def olderthan(file,ttl=86400*7):
    """ Chequea la fecha de modificacion de un archivo """
    try:
        statinfo = os.stat(file) 
        if (statinfo.st_size>10):
            modificado=time.gmtime(statinfo.st_mtime)
            ahora=time.gmtime()
            resta = (time.mktime(ahora) - time.mktime(modificado))
            segundos=int(resta)
            if(segundos > ttl):
                return True
            else:
                return False
    except OSError as e:
        print('No puedo abrir el archivo '+file)
        return True

def parse_asn_rir(CONFIG):
    asn16csv = CONFIG['url_deleg_iana_asn16']
    asn32csv = CONFIG['url_deleg_iana_asn32']
    feed = CONFIG['tabla_asn_iana']
    try:
        statinfo = os.stat(feed) 
        if (statinfo.st_size>100):
            if (olderthan(feed,CONFIG['feed_ttl'])):
#               print('El archivo '+feed+' tiene mas de '+CONFIG['feed_ttl']+' segundos desde su creacion, lo bajo de nuevo')
                os.remove(feed)
                for url in [asn16csv,asn32csv]:
                    download(url,feed,'a')
#            else:
#                print('El archivo '+feed+' tiene '+str(int(dias))+' dias, lo conservo')
    except OSError as e:
#        print('No puedo abrir el archivo '+feed+', lo creo')
        for url in [asn16csv,asn32csv]:
            download(url,feed,'a')
    try:
        with open(feed, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            dicasn = {0:""}
            for row in reader:
                colasn=row[0].rstrip()
                colrir=row[1].rstrip()
                colwhois=row[2].rstrip()

                if not (re.match('Assigned',colrir)):
                    continue

                if (re.match('^[0-9]+',colasn)):
                    ix=0
                    if(re.match('[0-9]+-',colasn)):
                        inicio,sep,fin = colasn.partition('-')
                        for ix in range (int(inicio),int(fin)+1):
                            dicasn[ix]=colrir[12:]
                    else:
                        dicasn[colasn]=colrir[12:]
            try:            
                with open(CONFIG['tabla_asn_json'], 'w') as fp:
                    json.dump(dicasn, fp)
            except IOError as e:
                print('Error en el archivo: '+str(e))
    except IOError as e:
        print('Error en el archivo: '+str(e))
                
    
def generate_ixp_report(CONFIG,PAIS):
    print("\n====== Reporte de "+PAIS+" ======\n")
    #ArchivoTablaIXP='bgp-ixp-'+PAIS+'.txt'
    ArchivoTablaIXP='bgp-ixp-'+PAIS
    
    #TODO Review and fix this
    [pais_ASNs,ASNpais]=make_asn_pais(CONFIG['deleg_lacnic'])
    try:
        with open(CONFIG['tmp_dir']+"RPT_Dict_RIR",'w') as f:
            f.write(repr(pais_ASNs))
        with open(CONFIG['tmp_dir']+"RPT_Dict_AS",'w') as f:
            f.write(repr(ASNpais))
    except IOError as e:
        print('Error en el archivo: '+str(e))
   
    [ASNsIXP,LinksIXP] = make_asn_links(CONFIG['feed_dir']+ArchivoTablaIXP)
    print ("Cantidad de ASNs en "+ArchivoTablaIXP+": "+str(len(ASNsIXP)))
    print ("Cantidad de Links en "+ArchivoTablaIXP+": "+str(len(LinksIXP)))
    
    try:
        with open(CONFIG['tmp_dir']+'asnsixp-'+PAIS+'.txt','w') as f:
            f.write(repr(ASNsIXP))
    except IOError as e:
        print('Error en el archivo: '+str(e))
    
    InterseccionAS = dict()
            
    for ctry in pais_ASNs.keys():
        # Obtenemos la interseccion entre los ASN's que un pais publica
        # en la tabla global y los que estan en el IXP
        InterseccionAS[ctry]=pais_ASNs[ctry] & ASNsIXP
                        
        if len(InterseccionAS[ctry]) > 0:
            print("Cantidad de ASN's de "+str(ctry)+" en el archivo "+str(ArchivoTablaIXP)+": "+str(len(InterseccionAS[ctry])))
    
        try:
            with open(CONFIG['tmp_dir']+"RPT_ASNs_"+PAIS+"_"+ArchivoTablaIXP,'w') as f:
                f.write(repr(InterseccionAS[ctry]))
            with open(CONFIG['tmp_dir']+"RPT_Links_"+PAIS+"_"+ArchivoTablaIXP,'w') as f:
                f.write(repr(LinksIXP))
        except IOError as e:
            print('Error en el archivo: '+str(e))

def is_asn32(asnumber):
    if(is_asdot(asnumber)):
        return True
        
    if(int(asnumber) > 65535):
        return True
    else: 
        return False
    
def is_asdot(asnumber):
    if (str(asnumber).find('.')):
        return True
    else:
        return False
    
def convert_to_asplain(asnumber):
    if(is_asn32(asnumber) == True):
        if (is_asdot(asnumber)):
            asdot = str(asnumber)
            region,resto = asdot.split('.')
            return int(region) * 65536 + int(resto)
        else:
            return asnumber
    else:
        return asnumber

def convert_to_asdot(asnumber):
    if(is_asn32(asnumber)):
        region = int(asnumber) // 65536
        resto = int(asnumber) % 65536
        return str(str(region)+"."+str(resto))
    else:
        return False
    
def find_rir_by_asn(CONFIG,asnumber):
    """ Encuentra a que RIR hay que hacer la consulta de RDAP
        de acuerdo el numero de sistema autonomo de la clase """
    reservados=[0,23456]
    reservados.extend(range(64512,65535))
    if int(asnumber) in reservados:
        return 'SPECIAL'
    else:
        try:
            with open(CONFIG['tabla_asn_json'], 'r') as archivo:
                data = json.load(archivo)
                if(data[asnumber]=='RIPE NCC'):
                    return 'RIPENCC'
                elif(data[asnumber])=='':
                    return 'NOTFOUND'
                return (data[asnumber])
        except Exception as e:
            pass

def find_rir_by_country(CONFIG,country):
    """ [TODO] Devuelve el nombre del RIR que atiende a un pais determinado """
    RIRs = ['ARIN','RIPENCC','APNIC','LACNIC','AFRINIC']
    
    for rir in RIRs:
        # TODO Implementar esta funcion
        # 1 abrir delegaciones
        # 2 procesar buscando Pais
        # 3 devolver resultados unicos
        next
    return 'LACNIC'

def update_data(url,file,ttl=86400*7):
    if olderthan(file,ttl):
        print('El archivo '+file+' tiene mas que los '+str(ttl)+' segundos requeridos.')
        print('Descargando '+file+'...')
        download(url,file,'w')
        return True
    else:
        return False
    
def make_asn_pais(archivo):
    """Arma dos Diccionarios [pais:{ASNs}] y [ASN:pais] desde el archivo de
    delegaciones de un RIR"""
    ListaDeASNdelPais={"":{}}
    PaisDelASN={0:""}
    with open(archivo) as rirfile:
        for line in rirfile:
            # lacnic|AR|ipv4|200.3.168.0|2048|20051007|allocated
            # lacnic|MX|asn|278|1|19890331|allocated
            [lacnic,CountryCode,tipo,asnumber,long,fecha]=line.split("|",5)
            if tipo != "asn":
                continue
            elif CountryCode in ListaDeASNdelPais:
                ListaDeASNdelPais[CountryCode].add(asnumber)
            else:
                ListaDeASNdelPais.update({CountryCode:{asnumber}})
            PaisDelASN[asnumber]=CountryCode
    del(ListaDeASNdelPais[""])
    return([ListaDeASNdelPais,PaisDelASN])

def make_asn_links(bgpdump):
    """[NEEDFIX] Devuelve dos conjuntos desde un dump BGP"""
    ListaASNs=[]
    ListaLinks=[]
    try:
        fileinfo=os.stat(bgpdump)
    except OSError as e:
        print('Error al acceder al archivo '+bgpdump+': '+str(e))
        return False
    
    dumptype = ribtype(bgpdump)
    
    if (dumptype == 'cisco'):
        ListaASNs,ListaLinks = parseCisco(bgpdump)   
        
    if (dumptype == 'mrt'):
        ListaASNs,ListaLinks = parseMRT(bgpdump)
        
    return([set(ListaASNs), set(ListaLinks)])

def rdapwhois(CONFIG,ASNs):
    cachedir=CONFIG['json_dir']
    RDAP404=set()
    DatosWHOIS=dict()
    
    #Verifico que exista el directorio
    try:
        fileinfo=os.stat(cachedir)
    except OSError as e:
        os.mkdir(cachedir)
    
    for asn in ASNs:
        # Busco a que rir pertenece el AS
        url=CONFIG['rdap_RIPENCC']+str(asn)
        if (asn != '0'):
            rir=find_rir_by_asn(CONFIG,asn)
        
        if (rir == 'SPECIAL'):
            next  
        elif (rir == 'NOTFOUND'):
            next        
        elif rir == 'ARIN':
            url=str(CONFIG['rdap_ARIN']+str(asn))
        elif rir == 'RIPENCC':
            url=str(CONFIG['rdap_RIPENCC']+str(asn))
        elif rir == 'APNIC':
            url=str(CONFIG['rdap_APNIC']+str(asn))
        elif rir == 'LACNIC':
            url=str(CONFIG['rdap_LACNIC']+str(asn))
        elif rir == 'AFRINIC':
            url=str(CONFIG['rdap_AFRINIC']+str(asn))
        else:
            print('No hay informacion de servidor RDAP para el AS'+str(asn)+' en el RIR: '+str(rir))
            next
    
#            if (not CONFIG['rdap_'+rir.upper()]):
#                print('No hay informacion de servidor RDAP para el RIR: '+rir)
#                return
#            url=str(CONFIG['rdap_'+rir]+str(asn))
        archivo=cachedir+str(asn)+'.json'
        
        try:            
            statinfo=os.stat(archivo)
            if(statinfo.st_size > 1000):
                w=open(archivo,'r')
                DatosWHOIS[asn]=json.loads(w.read())
                w.close()
#                print("Archivo: "+archivo + "| Tamanio: "+str(statinfo.st_size)+"\n")
            else:
                raise OSError('Archivo menor a 1000 bytes')

        except (IOError,OSError) as e:            
            try:
                request = urllib2.Request(url, headers={'Accept': 'application/json'})
                f = urllib2.urlopen(request)
                
                with open(archivo,'w') as w:
                    DatosWHOIS[asn]=f.read()
                    w.write(DatosWHOIS[asn])
                    
            except (urllib2.HTTPError,urllib2.URLError) as e:
                RDAP404.add(asn)
                print("No se pudo obtener '"+url+"' => "+ str(e))
                
            except (IOError,OSError) as e:
                print('Error en el archivo '+archivo+': ' + str(e))
                
            else:
                f.close()
        
        except Exception as e:
                print('Error: '+str(e))

#    if (len(RDAP404) > 0):
#        print('\nSe encontraron errores en las consultas RDAP para los siguientes ASNs:')
#	for asnumber in RDAP404:
#		print('\t--> AS'+str(asnumber))
    return(DatosWHOIS)
    
def update_feeds(CONFIG):
    """Actualiza los feeds de informacion desde sitios publicos de internet"""
    print('Verificando si hay archivos para descargar...')
    print("\t  * Delegaciones de los RIR")
    rehacer = False
    listadodeasn=set()
    for rir in ['arin','ripencc','apnic','lacnic','afrinic']:
        url=CONFIG['deleg_'+rir+'_url']
        archivo=CONFIG['deleg_'+rir]
        if (update_data(url,archivo,CONFIG['feed_ttl'])):
            rehacer = True
            
    if (rehacer == True):
            try:
                statinfo = os.path.isfile(CONFIG['main_feed'])
                if (statinfo):
                    os.remove(CONFIG['main_feed'])
            except IOError as e:
                print ('Error al acceder el archivo: '+CONFIG['main_feed']+': '+e)
                
#            mainfeed = open(CONFIG['main_feed'],'w')
            try:
                with open (CONFIG['tmp_dir']+'delegaciones','w') as mainfeed:

                    for rir in ['arin','ripencc','apnic','lacnic','afrinic']:
                        archivo=CONFIG['deleg_'+rir]
                        print("\t\t  --> Parseando "+archivo)

                        try:
                            with open(archivo,'r') as delegation:
                                contenido = delegation.readlines()
                                for linea in contenido:
                                    if not re.search(r'^(arin|ripencc|apnic|lacnic|afrinic)\|',linea):
                                        next
                                    else:
                                        if re.search(r'\|summary$',linea):
                                            next
                                        else:
                                            mainfeed.write(linea.strip()+"\n")
                        except IOError as e:
                            print ('Error al acceder el archivo: '+archivo+': '+e)
            except IOError as e:
                print('Error en el archivo: '+str(e))
                
    print("\t  * ASN's asignados por IANA")
    parse_asn_rir(CONFIG)
        
def unq(seq):
    """ Devuelve un set con elementos unicos """
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if not (x in seen or seen_add(x))]

def report_missing_asns(CONFIG,PAIS):
    f=open(CONFIG['tmp_dir']+"RPT_ASNs_"+PAIS+'_'+CONFIG['tabla_mundial'],'r')
    ASNsGlobalesDelPais=eval(f.readline())
    f.close()
    f=open(CONFIG['tmp_dir']+'asnsixp-'+PAIS+'.txt','r')
    ASNsDelIXP=eval(f.readline())
    f.close()
    
    upstreams=dict()
    try:
        with open(CONFIG['tmp_dir']+'RPT_Upstreams_'+PAIS,'r') as rpt:
            upstreams=eval(rpt.readline())
    except Exception as e:
            print('Error en el archivo: '+str(e))
            
    ASNsFaltantesEnElIXP = ASNsGlobalesDelPais - ASNsDelIXP
    noestanenelixp=list()
    
    ProveedoresDeAsnFaltantes=dict()
    ProveedoresQueNoAnuncianUnASN=dict()
    ProveedorInternacional=set()
    for asn in ASNsFaltantesEnElIXP:
        noestanenelixp.append(asn)
        for upst in upstreams[asn]:
            if not (upst in ASNsGlobalesDelPais):
                ProveedorInternacional|={upst}
            ListaProveedores=[upst]
            procesados=[upst]
            for proveedor in ListaProveedores:
                if proveedor in ASNsDelIXP:
                    ProveedoresDeAsnFaltantes[asn]=proveedor
                    if proveedor in ProveedoresQueNoAnuncianUnASN:
                        ProveedoresQueNoAnuncianUnASN[proveedor]|={asn}
                    else:
                        ProveedoresQueNoAnuncianUnASN[proveedor]={asn}
                    break
                elif proveedor in procesados:
                    break
                elif len(ListaProveedores)>20:
                    print('Error: Demasiados Upstreams para procesar el ASN '+str(upst))
                    print('Listado: '+str(ListaProveedores))
                    break
                ListaProveedores=list(upstreams[proveedor])
                procesados+=[proveedor]
    print('\nProveedores Internacionales de los ASN que no estan en en IXP de '+str(PAIS)+':')
    for carrier in ProveedorInternacional:
        nombre=nombreasn(CONFIG,carrier)
        print('\t--> AS'+str(carrier)+nombre)
        
    print('\nCantidad de ASNs que estan en el IXP de '+str(PAIS)+' y no anuncian a todos los clientes: '+str(len(ProveedoresQueNoAnuncianUnASN.keys()))+'\n')
    for isp in ProveedoresQueNoAnuncianUnASN.keys():
        nombre=nombreasn(CONFIG,isp)
        print('\nEl AS'+str(isp)+nombre+' no esta anunciando los siguientes ASNs en el IXP de '+str(PAIS)+': ')
        for numero in ProveedoresQueNoAnuncianUnASN[isp]:
            nombre=nombreasn(CONFIG,numero)
            print('\t --> AS'+str(numero)+nombre)
    
    noestanenelixp.sort()
    
    datoswhois = rdapwhois(CONFIG,ASNsFaltantesEnElIXP)
    print('\nASNs que publican al mundo y no estan directamente conectados al IXP de '+PAIS+': '+str(len(ASNsFaltantesEnElIXP)))
    
    try:
        with open(CONFIG['tmp_dir']+"RPT_ASNs_"+PAIS+'_faltantes','w') as f:
            f.write(repr(noestanenelixp))
        with open(CONFIG['tmp_dir']+"RPT_ASNs_"+PAIS+'_nopublican','w') as f:
            f.write(repr(ProveedoresQueNoAnuncianUnASN))
    except Exception as e:
        print('Error: ',str(e))
    
    for faltante in noestanenelixp:
        try:
            with open(CONFIG['json_dir']+faltante+'.json','r') as j:
                jdata = json.load(j)
                print('\t --> AS'+faltante+' '+jdata['entities'][0]['vcardArray'][1][5][3][0].encode('utf-8'))
                print('\t\t Ciudad: '+jdata['entities'][0]['vcardArray'][1][2][3][3].encode('utf-8')+', '+jdata['entities'][0]['vcardArray'][1][2][3][4].encode('utf-8')+' - '+jdata['entities'][0]['vcardArray'][1][2][3][6].encode('utf-8'))
                print('\t\t Telefono: '+jdata['entities'][0]['vcardArray'][1][4][3].encode('utf-8'))
                print('\t\t Tecnico: '+jdata['entities'][2]['vcardArray'][1][1][3].encode('utf-8'))
                print('\t\t Email: <'+jdata['entities'][2]['vcardArray'][1][3][3].lower()+'>')
        except IOError as e:
            print('\t --> [RDAP-Bug] Error al leer el JSON de AS'+str(faltante)+', reportar al RIR')
        except Exception as e:
            print('Error: ',str(e))

def parseMRT(bgpfile):
    """Devuelve dos conjuntos desde un dump BGP"""
    ListaASNs=[]
    ListaLinks=[]
    with open(bgpfile,'r') as dump:
        dumplines = dump.readlines()
        for linea in dumplines:
            linea = linea.strip()
            aspath= txtxtract(linea,'ASPATH: ',';')
            asns = aspath.split()
            lastasn=0
            for asn in asns:
                if(asn[0] == '{'):
                    asset=txtxtract(asn,'{','}')
                    while asset:
                        componente,sp,asset=asset.partition(",")
                        ListaASNs+=[componente]
                        if(componente != lastasn):
                            ListaLinks+=[lastasn+','+componente]
                else:
                    ListaASNs+=[asn]
                    if(lastasn > 0 and asn != lastasn):
                        ListaLinks+=[lastasn+','+asn]
                    lastasn=asn            
    return([set(ListaASNs), set(ListaLinks)])

def parseCisco(bgpfile):
    """Devuelve dos conjuntos desde un dump BGP"""
    ListaASNs=[]
    ListaLinks=[]
    offset=0
    with open(bgpfile,'r') as dump:
        dumplines = dump.readlines()
        while offset < 1:
            for linea in dumplines:
                linea = linea.strip()
                if(re.search(r'.*Path.*',linea)):
                    offset=linea.find('Path')
                    break
                    
        for linea in dumplines:
            if(re.search(r'^.*(i|\?)$',linea)):
                aspath=linea[offset:-2]
                asns = aspath.split()
                lastasn=0
                for asn in asns:
                    if(asn[0] == '{'):
                        asset=txtxtract(asn,'{','}')
                        while asset:
                            componente,sp,asset=asset.partition(",")
                            ListaASNs+=[componente]
                            if(componente != lastasn):
                                ListaLinks+=[lastasn+','+componente]
                    else:
                        ListaASNs+=[asn]
                        if(lastasn > 0 and asn != lastasn):
                            ListaLinks+=[lastasn+','+asn]
                        lastasn=asn
        return([set(ListaASNs), set(ListaLinks)])

def txtxtract(texto,st,en):
    """Extrae un pedazo de texto dado un atributo de MRT"""
    chunk = texto.strip()
    inicio = chunk.find(st)
    if(inicio < 1):
            return ''
    minichunk = chunk[inicio:]
    fin = minichunk.find(en)
    if(fin < 1):
            return ''
    buscado = minichunk[len(st):fin]
    return str(buscado)

def ribtype(archivo):
    minhits=5
    chits=0
    mhits=0
    lin=0
    try:
        with open(archivo,'r') as dump:
            contenido = dump.readlines()
            totaldelineas=len(contenido)
            for linea in contenido:
                lin+=1
                linea = linea.strip()
                if(chits >= minhits):
                    return 'cisco'
                if(mhits >= minhits):
                    return 'mrt'
                if(re.search(r'^.*(i|\?)$',linea)):
                    chits+=1
                if(re.search(r'^.*ASPATH:.*',linea)):
                    mhits+=1
                if(lin>minhits*4):
                    return False
                    break
    except IOError as e:
        print('No puedo abrir el archivo '+archivo+': '+e)

def foldercheck(CONFIG):
    """Checks the existence of a list of folders, if they not exists this function will create it"""
    folders = set()
    for clave in CONFIG.keys():
        if(re.search(r'.*_dir.*',clave)):
            folders.add(clave)
    
    for folder in folders:
        try:
            if not os.path.exists(CONFIG[folder]):
                os.makedirs(CONFIG[folder])
        except OSError as e:
            print('Problemas con la carpeta '+folder+': '+str(e))
            
def cidrsOverlap(cidr0, cidr1):
    """ Determina si un prefijo es componente de otro"""
    return cidr0.first <= cidr1.last and cidr1.first <= cidr0.last

def nombreasn(CONFIG,numero):
    """ Returns the owner name of an ASN """
    try:
        with open(CONFIG['json_dir']+numero+'.json','r') as j:
            datos=json.load(j)
            owner=datos['entities'][0]['vcardArray'][1][5][3][0].encode('utf-8').title()
            return ' ('+owner+') '
    except:
        rdapwhois(CONFIG,[numero])
        return ' () ' #TODO Maybe needs a query in RDAP?

def checkrequiredfiles(CONFIG):
	pass	

def make_asn_graphs(CONFIG,pais):
        output =CONFIG['webreport_dir']+'data/ixp-'+pais+'/'
        PathASNsIXP = CONFIG['tmp_dir']+'asnsixp-'+pais+'.txt'
        PathASNsGlobal = CONFIG['tmp_dir']+'RPT_ASNs_'+pais+'_full-routing-cisco.txt'
        PathLinksASNsIXP = CONFIG['tmp_dir']+'RPT_Links_'+pais+'_bgp-ixp-'+pais
        PathLinksASNsGlobal = CONFIG['tmp_dir']+'RPT_Links_bgp-ixp-'+pais

        print("\n==== Generando datos para el grafo de "+pais+" ====")
        ### Traigo todos los asn de un IXP
        ASNsIXP=set()
        f=open(PathASNsIXP,"r")
        ASNsIXP=eval(f.read())
        
        ### Traigo todos los asn de un pais
        ASNsGlobal=set()
        f=open(PathASNsGlobal,"r")
        ASNsGlobal=eval(f.read())

        ### Traigo todos los links de un IXP
        LinksASNsIXP=set()
        f=open(PathLinksASNsIXP,"r")
        LinksASNsIXP=eval(f.read())
        
        ### Traigo todos los links de un pais
        LinksASNsGlobal=set()
        f=open(PathLinksASNsGlobal,"r")
        LinksASNsGlobal=eval(f.read())

        dictLinks = dict()
        listaLinks=list(dict())
        listaASNsEnIXP = set()
        
        ### Armo los depends para el grafo, a cada AS le corresponde un set de depends
        for link in LinksASNsIXP:
            depends,sp,asOrigen=link.partition(",")      

            if asOrigen in dictLinks.keys():
                dictLinks[asOrigen] |= {'AS'+depends}
            else:
                dictLinks[asOrigen] = {'AS'+depends}
            listaASNsEnIXP.add(depends)
            listaASNsEnIXP.add(asOrigen)
                
        nodosFaltantes = 0
        dictFaltantes = dict()
        listFaltantes = set()
        listFaltantesSinDepends = set()
        
        ### Obtengo los ASNs que no estan el IXP y los cuento
        for asn in ASNsGlobal:
            if asn not in listaASNsEnIXP:                
                listFaltantes.add(asn)
                nodosFaltantes = nodosFaltantes +1
        
        for link in LinksASNsGlobal:
            depends,sp,asOrigen=link.partition(",")      

            if asOrigen in listFaltantes:
                if depends in dictLinks.keys():
                    if asOrigen in dictFaltantes.keys():
                        dictFaltantes[asOrigen] |= {'AS'+depends}
                    else:
                        dictFaltantes[asOrigen] = {'AS'+depends}
                else:
                    listFaltantesSinDepends.add(asOrigen)

        print('---> Cantidad de nodos del IXP: ' + str(len(dictLinks)))
        print('---> Cantidad de nodos fuera del IXP: ' + str(nodosFaltantes))

        ASNsCABASE = ["AS11058","AS52294","AS52324","AS52332","AS52359","AS52360","AS52370","AS52374","AS52375","AS52376","AS52403","AS52404","AS52500","AS61441"]

        ### Armo el listado con el formato requerido por la aplicacion
        for asn,links in dictLinks.iteritems():            
            for otroasn in links:
                if otroasn in ASNsCABASE:
                    tipo=3
                else:
                    tipo=1            
                
            if "AS"+asn in ASNsCABASE:
                    tipo = 4
                    
            if len(links) > 0:
                listaLinks += [{"depends":list(links),"type":str(tipo),"name":'AS'+asn}]
            else:
                listaLinks += [{"depends":[],"type":str(tipo),"name":'AS'+asn}]
                
        for asn,links in dictFaltantes.iteritems():
            if len(links) > 0:
                listaLinks += [{"depends":list(links),"type":"2","name":'AS'+asn}]
            else:
                listaLinks += [{"depends":[],"type":"2","name":'AS'+asn}]
                
#        for asn in listFaltantes:
#            listaLinks += [{"depends":[],"type":"2","name":'AS'+asn}]

        for asn in listFaltantesSinDepends:
            listaLinks += [{"depends":[],"type":"5","name":'AS'+asn}]
            
        try:
            listaLinks.remove({"depends":["AS0"],"type":"1","name":"AS52324"})                        
        
        except Exception as e:
            pass
            #print(str(e))
        
        #TODO ver lo del as desde cual se toma el archivo, para ponerlo en la lista como {"depends":[],"type":"1","name":"AS52324"} o {"depends":[],"type":"1","name":"AS19411"} 
        if pais == 'AR':
            listaLinks += [{"depends":[],"type":"1","name":"AS52324"}]
        elif pais == 'CL':
            listaLinks += [{"depends":[],"type":"1","name":"AS19411"}]
        elif pais == 'CO':
            listaLinks += [{"depends":[],"type":"1","name":"AS18747"}]

        ### Creo el json para la aplicacion
        if not os.path.exists(output):
            os.makedirs(output)
        with open(output + 'objects.json','w') as j:
            j.write(json.dumps(listaLinks))
            
def make_mkdn_files(CONFIG):   
    print("\n==== Generando datos de whois para los grafos ====")
    for file in os.listdir(CONFIG['json_dir']):
        try:            
            for pais in CONFIG['countries_to_report']:
                output =CONFIG['webreport_dir']+'data/ixp-'+pais+'/'
                if not os.path.exists(output):
                    os.makedirs(output)
                
                asn,sp,extension=file.partition('.')
                
                if not os.path.isfile(output + 'AS' + asn + '.mkdn'):
                    with open(CONFIG['json_dir'] + '/' + file,'r') as j:
                        jdata=json.load(j)                      

                        info_html = '<ul><li>Nombre: '+jdata['entities'][0]['vcardArray'][1][5][3][0]+'<br /></li>'
                        info_html += '<li>Ciudad: '+jdata['entities'][0]['vcardArray'][1][2][3][3]+', '+jdata['entities'][0]['vcardArray'][1][2][3][4]+' - '+jdata['entities'][0]['vcardArray'][1][2][3][6]+'<br /></li>'
                        info_html += '<li>Telefono: '+jdata['entities'][0]['vcardArray'][1][4][3]+'<br /></li>'
                        info_html += '<li>Tecnico: '+jdata['entities'][2]['vcardArray'][1][1][3]+'<br /></li>'
                        info_html += '<li>Email: '+jdata['entities'][2]['vcardArray'][1][3][3].lower()+'<br /></li></ul>'
                    
                    with open(output + 'AS' + asn + '.mkdn','w') as j:
                        j.write(info_html.encode('utf-8'))
                
                if not os.path.isfile(output + 'config.json'):
                    with open('config.json','r') as j:
                        with open(output + 'config.json','w') as r:
                            r.write(j.read())
                        
        except ValueError as e:
#            print('ValueError: ' + str(e) + ' AS' + asn)
            continue
        except KeyError as e:
#            print('KeyError: ' + str(e) + ' AS' + asn)
            continue
        except Exception as e:
#            print('Error: ' + str(e))
            continue
