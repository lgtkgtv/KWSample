# coding: utf-8

import urlparse
import urllib
import urllib2
import os.path
import socket
import json
import sys


class KWAPI:
    def __init__(self, review_url, user, logger=None):
        self.review_url = review_url
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug('Specified Review Server URL:%s, Specified Review User:%s' % (review_url, user))
        
        '''
        Normalize Review API URL
        '''
        scheme, server, path, query, anchor = urlparse.urlsplit(self.review_url)
        host, portstr = server.split(':')
        if host == 'localhost':
            host = socket.gethostbyname(socket.gethostname())
        if portstr == '':
            port = 8080
        else:
            port = int(portstr)
        if path == '':
            self.review_url = self.review_url + "/review/api"
        
        '''
        Get Auth token from ltoken file
        '''
        ltokenpath = os.path.normpath(os.path.expanduser("~/.klocwork/ltoken"))
        
        if not os.path.lexists(ltokenpath):
            self.logger.error("Cannot find ltoken file. Please run kwauth to generate the ltoken file.")
            raise KWAPIError,'Cannot find ltoken file. Please run kwauth to generate the ltoken file.'
      
        ltokenFile = open(ltokenpath, 'r')
        auth_token_found = False
        for line in ltokenFile:
            elems = line.strip().split(';')
            host_in_ltoken = elems[0]
            port_in_ltoken = elems[1]
            user_in_ltoken = elems[2]
            self.logger.debug("host in ltoken: %s, port in ltoken:%s, user in ltoken:%s" % ( host_in_ltoken, port_in_ltoken, user_in_ltoken))
            if host_in_ltoken == host and port_in_ltoken == str(port) and user_in_ltoken == user:
                self.auth_token = elems[3]
                self.user = user_in_ltoken
                auth_token_found = True
                break;
        ltokenFile.close()
        
        if auth_token_found == False:
            self.logger.error("Specified information does not match with the value in ltoken file. Please run with --debug option for more information or run kwauth to recreate ltoken for the desired server.")
            raise KWAPIError, 'Error in finding auth information from ltoken file'
            


    def search_defects(self, project_name, query_conditions):
        request_parms = {}
        request_parms["action"] = "search"
        request_parms["project"] = project_name
        request_parms["query"] = query_conditions
        return self.send_request(request_parms)

    def get_ncnbloc_for_project_by_aggregate(self, project_name):
        request_parms = {}
        request_parms["action"] = "metrics"
        request_parms["project"] = project_name
        request_parms["aggregate" ] = "true"
        request_parms["query"] = "metric:NCNBLOC_FILE"
        response  = self.send_request(request_parms)

        loc = 0.0
        for record in response:
            json_loc = json.loads(record)
            loc = json_loc["sum"]
            break
        return loc


    def get_ncnbloc_for_project(self, project_name):
        request_parms = {}
        request_parms["action"] = "metrics"
        request_parms["project"] = project_name
        request_parms["query"] = "metric:NCNBLOC_FILE"
        response  = self.send_request(request_parms)

        loc = 0.0
        for record in response:
            json_loc = json.loads(record)
            loc += json_loc["metricValue"]
        return loc


    def get_build_ids_for_project(self, project_name, last_days=-1):
        request_parms = {}
        request_parms["action"] = "builds"
        request_parms["project"] = project_name
        response  = self.send_request(request_parms)
        build_ids = []
        for record in response:
            json_build = json.loads(record)
            if last_days != -1:
                curdate = datetime.utcnow().date()
                basedate = curdate -  timedelta(days=last_days)
                builddate = date.fromtimestamp(json_build["date"]/1000)
                if builddate < basedate: #older than basedate?
                    continue
            build_ids.append(json_build["id"])
        return build_ids


    def send_request(self, options):
        """
        Sending a request to Klocwork Review Server with specified options
        """
        options["user"] = self.user
        if self.auth_token is not None :
            options["ltoken"] = self.auth_token

        try :
            data = urllib.urlencode(options)
            req = urllib2.Request(self.review_url, data)
            self.logger.debug('Sending request to server \"%s\" with data: \"%s\"' % (req.get_full_url(), req.get_data()))
            return urllib2.urlopen(req)
        except Exception as e:
            self.logger.error("Could not establish connection with Klocwork Server for :\n" + str(e) + "\nPlease check <project_root>\logs\klocwork.log as well.")
            return None

    def export_checker_config(self, project_name):
        """
        Get a list of all checker configuration for the specified project
        """
        request_parms = {}
        request_parms["action"] = "defect_types"
        request_parms["project"] = project_name
        return self.send_request(request_parms)
        
    def update_checker_setting(self, project_name, checker_name, enabled):
        """
        Update checker setting for the specified checker in the project
        """
        request_parms = {}
        request_parms["action"] = "update_defect_type"
        request_parms["project"] = project_name
        request_parms["code"] = checker_name
        request_parms["enabled"] = enabled
        return self.send_request(request_parms)



class KWAPIError(Exception): pass


