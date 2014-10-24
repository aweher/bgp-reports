#! /usr/bin/env python
# -*- coding: utf-8 -*-
def unq(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if not (x in seen or seen_add(x))]

def cidrsOverlap(cidr0, cidr1):
    return cidr0.first <= cidr1.last and cidr1.first <= cidr0.last

def Whois (RIR,ASNs):
  WI=dict()
  DIRWI="WHOIS/"
  WI["lacnic"]="http://restfulwhoisv2.labs.lacnic.net/restfulwhois/autnum/"

  try: 
    statinfo = os.stat(DIRWI) 
  except OSError as e:
    os.mkdir(DIRWI)

  if ( not WI[RIR] ):
    print ("No info para",RIR)
    return
  for AS in ASNs:
    url=WI[RIR]+str(AS)
    i = url.rfind("/")
    file = DIRWI+str(AS)+".json"
    try: 
      statinfo = os.stat(file) 
      if (statinfo.st_size>1000):
        w=open(file,"r")
        try:
          DicWhois[AS]=json.loads(w.read())
        except ValueError, e:
          print (file,":",e)
        continue
    except OSError as e:
      #print (AS," from ",RIR)
      asdf=False # no queria indentar...

    #print (file)
    opener = urllib2.build_opener()
    try:
      req = urllib2.Request(url, headers={'Accept': 'application/json'})
      f = urllib2.urlopen(req)
    except urllib2.HTTPError as e:
      #print e.code
      #print e.read() 
      RDAP404.add(AS)
    else:
      w=open(file,"w")
      try:
        w.write(f.read())
      except OSError as e:
        print(e)
      f.close()
      w.close()
  return(DicWhois)

def DicASNsRIR(file):
  """Arma dos Diccionarios [pais:{ASNs}] y [ASN:pais] del archivo de delegaciones de LACNIC"""
  DicRIR={"":{}}
  DicAS={0:""}
  with open(file) as rirfile:
    for line in rirfile:
      # lacnic|AR|ipv4|200.3.168.0|2048|20051007|allocated
      # lacnic|MX|asn|278|1|19890331|allocated
      [lacnic,CountryCode,tipo,asnumber,long,fecha]=line.split("|",5)
      if tipo != "asn":
        continue
      elif CountryCode in DicRIR:
        DicRIR[CountryCode].add(asnumber)
      else:
        DicRIR.update({CountryCode:{asnumber}})
      DicAS[asnumber]=CountryCode

  del(DicRIR[""])
  return([DicRIR,DicAS]);        

def setsbgp(bgpfile):
  """Devuelve dos conjuntos desde un dump BGP"""
  ListaASNs=[]
  ListaLinks=[]

  startASP=0
  with open(bgpfile) as dumpbgp:
    for line in dumpbgp:
      line=line.rstrip('\r\n')
      startASP=line.find("Path")
      if startASP > 40 :
        break
    if startASP<40:
      print("Error en archivo BGP - Falta texto Path en:",bgpfile)
      exit

    for line in dumpbgp:
      path=line[startASP:-2]
      cAS=1

      while path:
        as1,sp,path=path.partition(" ")
        if as1.isalnum():
          ListaASNs+=[as1]
          if cAS > 1:
            ListaLinks+=[as0+","+as1]
          as0=as1
          cAS+=1
        elif as1[0]=="{":
          path=as1[1:-1]
          while path:
            as1,sp,path=path.partition(",")
            if as1.isalnum():
              ListaASNs+=[as1]
              ListaLinks+=[as0+","+as1]
            else:
              print ("Warning-AS-Set parse error: ",line)
        else:
              print ("Warning-AS Path parse error: ",line)

#Utiliza listas en lugar de Conjuntos por el tiempo de procesamiento
# L.add es de O(1) y L|= es de O(n)
  return([set(ListaASNs), set(ListaLinks)])

if __name__ == "__main__":
  import sys
  import urllib2
  import json
  import os
 # import pybgpdump
  from netaddr import IPNetwork, IPAddress
  
  RDAP404=set()
#  print cidrsOverlap(IPNetwork('192.168.2.0/24'), IPNetwork('192.168.3.0/24')) # False
#  print cidrsOverlap(IPNetwork('192.168.2.0/23'), IPNetwork('192.168.3.0/24')) # True
  
  feed_dir='feeds/'
  BGPIXP='bgp-cabase'
  PAIS="AR"
  #BGPIXP='bgp-pitchile'
  #PAIS="CL"
  BGPGLOBAL='rutas-level3.txt'
#  BGPGLOBAL='bgp-global'
  RIR="lacnic"
  LACNIC=feed_dir+'delegated-lacnic-latest'

  rpt_folder='reportes/'
  htmli_folder='htmlincludes/'
  HTML_OUT='reporte-bgp.html'
  HTML_IN_1='header.html'
  HTML_IN_2='footer.html'

  [DicRIR,DicAS]=DicASNsRIR(LACNIC)
  f=open(rpt_folder+"RPT_Dict_RIR",'w')
  f.write(repr(DicRIR))
  f=open(rpt_folder+"RPT_Dict_AS",'w')
  f.write(repr(DicAS))

  [ASNsIXP,LinksIXP] = setsbgp(feed_dir+BGPIXP)
  print ("Cantidad de ASNs",BGPIXP,":",len(ASNsIXP))
  print ("Cantidad de Links",BGPIXP,":",len(LinksIXP))

  for Pais in DicRIR.keys():
    PaisIXP = DicRIR[Pais] & ASNsIXP
    if len(PaisIXP) > 0:
      print ("Cantidad de ASNs de",Pais,"en",BGPIXP,":",len(PaisIXP))
  PaisIXP = DicRIR[PAIS] & ASNsIXP
  
  #escribe los reportes
  f=open(rpt_folder+"RPT_ASNs_"+PAIS+"_"+BGPIXP,'w')
  f.write(repr(PaisIXP))
  f=open(rpt_folder+"RPT_Links_"+PAIS+"_"+BGPIXP,'w')
  f.write(repr(LinksIXP))

# Para evitar el procesamiento completo de la tabla global comentar
# la siguiente linea y descomentar las otras 4
  [ASNsGL,LinksGL]=setsbgp(feed_dir+BGPGLOBAL)
#  f=open(rpt_folder+"RPT_ASNsGlobal",'r') #lee archivos pre procesados
#  ASNsGL=eval(f.readline())
#  f=open(rpt_folder+"RPT_LinksGlobal",'r')
#  LinksGL=eval(f.readline())

  print ("Cantidad de ASNs",BGPGLOBAL,":",len(ASNsGL))
  print ("Cantidad de Links",BGPGLOBAL,":",len(LinksGL))
  f=open(rpt_folder+"RPT_ASNsGlobal",'w')
  f.write(repr(ASNsGL))
  f=open(rpt_folder+"RPT_LinksGlobal",'w')
  f.write(repr(LinksGL))

# De la lista Global de Links genera: 
    # ASNs de border
    # Upstream de cada AS
    # Links dentro de un pais 
  Upstream={"":[]}
  ASNs_BORDER=list()
  Links_Pais=list()
  for links in LinksGL:
    as0,sp,as1=links.partition(",")
    if as1 in Upstream:
      Upstream[as1]|={as0}
    else:
      Upstream[as1]={as0}

    if ((as0 in DicRIR[PAIS]) or (as1 in DicRIR[PAIS])):
      ASNs_BORDER+=[as0,as1]
      Links_Pais+=[links]  
 
  f=open(rpt_folder+"RPT_ASNs_"+PAIS+"_BORDER","w")
  f.write(repr(ASNs_BORDER))
  f=open(rpt_folder+"RPT_Links_"+PAIS,"w")
  f.write(repr(Links_Pais))

  PaisGL = DicRIR[PAIS] & ASNsGL
  print ("Cantidad de ASNs de",PAIS,"en",BGPGLOBAL,":",len(PaisGL))
  f=open(rpt_folder+"RPT_ASNs_"+PAIS+"_"+BGPGLOBAL,'w')
  f.write(repr(PaisGL))

  DicWhois={"":{"":""}}
  DicWhois=Whois(RIR,list(PaisGL))
  WHOIS='DicWhois.json'
  f=open(WHOIS,"w")
  f.write(json.dumps(DicWhois))

  FaltanIXP = PaisGL - ASNsIXP
  print ("Cantidad de ASNs de",PAIS,"que faltan en",BGPIXP,":",len(FaltanIXP))
  f=open(rpt_folder+"RPT_ASNs_"+PAIS+"_faltan_"+BGPIXP,'w')
  f.write(repr(FaltanIXP))
 
  ProveedoresDeAsnFaltantes={"":""}
  ProveedoresQueNoAnuncianUnASN={"":{}}
  ProInt={""}
  for AsnQueNoEstaEnElIXP in FaltanIXP:
#    print("AS",faltante,"anunciado por",Upstream[faltante])
    for upst in Upstream[AsnQueNoEstaEnElIXP]:
      if not(upst in DicRIR[PAIS]):
        ProInt|={upst}
# Busca entre los ASN a la izquierda del ASPATH cuales están anunciados en IXP
# Se va armando la ListaUpstream con los AS que anuncian a cada ASN en el ASPath
      ListaUpstream=[upst]
      Procesados=[upst]
      for proveedor in ListaUpstream:
# Terminar cuando encontró uno que está en el IXP
        if proveedor in ASNsIXP:
          ProveedoresDeAsnFaltantes[AsnQueNoEstaEnElIXP]=proveedor
          if proveedor in ProveedoresQueNoAnuncianUnASN:
            ProveedoresQueNoAnuncianUnASN[proveedor]|={faltante}
          else:
            ProveedoresQueNoAnuncianUnASN[proveedor]={faltante}
          break
# Terminar cuando encuentra uno ya procesado
        elif proveedor in Procesados:
          break        
# Terminar cuando la lista de Upstreams está muy grande
        elif len(ListaUpstream)>20:
          print("Error: Demasiados Upstream para procesar ASN",upst,"Lista",ListaUpstream)
          break
        ListaUpstream+=list(Upstream[proveedor])
        Procesados+=[proveedor]

  print ("Proveedores Internacionales de los faltantes",ProInt)
  print ("Proveedores que estan en el IXP y no anuncian a los faltantes:",len(ProveedoresQueNoAnuncianUnASN.keys()))
  for isp in ProveedoresQueNoAnuncianUnASN.keys():
    print("El proveedor",isp,"deberia anunciar",ProveedoresQueNoAnuncianUnASN[isp])
 
  print("AS's no encontrados en RESTFul WHOIS: ",len(RDAP404),unq(RDAP404))
 
  f=open(rpt_folder+"RPT_ASNs_"+PAIS+"_DictFaltantes",'w')
  f.write(repr(ProveedoresDeAsnFaltantes))

  f=open(rpt_folder+"RPT_ASNs_"+PAIS+"_DictCanutos",'w')
  f.write(repr(ProveedoresQueNoAnuncianUnASN))

#########
  fr=open(htmli_folder+HTML_IN_1,'r')
  fw=open(htmli_folder+HTML_OUT,'w')
  fw.write(fr.read())
  for proveedor in ASNsIXP:
    fw.write('graph.addNode(\''+proveedor+'\');\n');
  for link in LinksIXP:
    fw.write('graph.addLink('+link+');\n');
 
  fr=open(htmli_folder+HTML_IN_2,'r')
  fw.write(fr.read())
  print"Listo"