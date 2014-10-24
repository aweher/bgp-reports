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

__author__="a.weher"
__date__ ="$Sep 1, 2014 11:38:27 AM$"

if __name__ == "__main__":
    import asnutils
    
# Main configuration
    CONFIG=dict()
    CONFIG['feed_dir']='feeds/' # Where to put the downloaded routing tables and rir assignments
    CONFIG['feed_ttl']=3600*24*31 #Seconds needed to download all the feeds again
    CONFIG['json_dir']='cache/'
    CONFIG['tmp_dir']='workdir/' # Temporal directory for internal reports
    CONFIG['webreport_dir']='webgraphs/'
    
    # These are countries for which you have the IXP routing table
#    CONFIG['countries_to_report']=['AR','BR','CL','CO']
    CONFIG['countries_to_report']=['AR','CL','CO']
    
    # BGP Global table file, there are two formats available. MRT is the smaller one.
    CONFIG['tabla_mundial']='full-routing-cisco.txt'
    #CONFIG['tabla_mundial']='full-routing-mrt.txt'
    
    # List of resources delegated by RIR
    CONFIG['deleg_arin_url']='ftp://ftp.apnic.net/pub/stats/arin/delegated-arin-extended-latest'
    CONFIG['deleg_apnic_url']='ftp://ftp.apnic.net/pub/stats/apnic/delegated-apnic-latest'
    CONFIG['deleg_ripencc_url']='ftp://ftp.ripe.net/ripe/stats/delegated-ripencc-latest'
    CONFIG['deleg_lacnic_url']='ftp://ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-latest'
    CONFIG['deleg_afrinic_url']='ftp://ftp.apnic.net/pub/stats/afrinic/delegated-afrinic-latest'
    CONFIG['deleg_arin']=CONFIG['feed_dir']+'delegated-arin-latest'
    CONFIG['deleg_apnic']=CONFIG['feed_dir']+'delegated-apnic-latest'
    CONFIG['deleg_ripencc']=CONFIG['feed_dir']+'delegated-ripencc-latest'
    CONFIG['deleg_lacnic']=CONFIG['feed_dir']+'delegated-lacnic-latest'
    CONFIG['deleg_afrinic']=CONFIG['feed_dir']+'delegated-afrinic-latest'
    
    # IANA ASN's List
    CONFIG['tabla_asn_iana']=CONFIG['feed_dir']+'asn-rir.csv'
    CONFIG['tabla_asn_json']=CONFIG['json_dir']+'asn-rir.json'
    CONFIG['url_deleg_iana_asn16']='http://www.iana.org/assignments/as-numbers/as-numbers-1.csv'
    CONFIG['url_deleg_iana_asn32']='http://www.iana.org/assignments/as-numbers/as-numbers-2.csv'
    CONFIG['main_feed']=CONFIG['json_dir']+'main_feed.json'
    
    # RDAP URL's
    CONFIG['rdap_ARIN']='http://whois.arin.net/rest/asn/AS'
    CONFIG['rdap_RIPENCC']='http://rest.db.ripe.net/search.json?query-string=as'
    CONFIG['rdap_APNIC']=CONFIG['rdap_RIPENCC'] # Todavia no esta implementada la busqueda de ASN, solo IPs: http://www.apnic.net/apnic-info/whois_search/about/rdap
    CONFIG['rdap_LACNIC']='http://rdap.labs.lacnic.net/rdap/autnum/'
    #CONFIG['rdap_LACNIC'] = 'http://restfulwhoisv2.labs.lacnic.net/restfulwhois/autnum/'
    CONFIG['rdap_AFRINIC']=CONFIG['rdap_RIPENCC'] #aun no desarrollado, parece que sirve el de ripe igual 

# Main
    asnutils.foldercheck(CONFIG)
    asnutils.update_feeds(CONFIG)
    asnutils.parse_asn_rir(CONFIG)
    asnutils.generar_reporte_global(CONFIG)
    
    for PAIS in CONFIG['countries_to_report']:
        asnutils.generate_ixp_report(CONFIG,PAIS)
        asnutils.generar_reporte_pais(CONFIG,PAIS)
        asnutils.report_missing_asns(CONFIG,PAIS)
        asnutils.make_asn_graphs(CONFIG,PAIS)
        
    asnutils.make_mkdn_files(CONFIG)
    
    print"\nHave a nice day"
    exit
