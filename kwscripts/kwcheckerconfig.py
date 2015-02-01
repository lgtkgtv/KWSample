# coding: utf-8

""" 
[NAME] Sample script for exporting/importing checker setting for a project

[DESCRIPTION] See usage by running this script with --help
Input/Output format for checker configuration is

[checker_name 1],(True or False]
[checker_name 2],(True or False]
...

For example:
ABV.ANY_SIZE_ARRAY,False
ABV.GENERAL,True

"""
import argparse
import logging
import json

import kwapiwrapper


def main():
    '''
    Command Options
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("--url",
                        action="store",
                        dest="review_server_url",
                        required=True,
                        help="specify URL of Klocwork Review Server as http://<hostname>:<port>")
    parser.add_argument("--project",
                        action="store",
                        dest="review_server_project",
                        required=True,
                        help="speicfy projet name on Klocwork Review Server")
    parser.add_argument("--user",
                        action="store",
                        dest="user",
                        nargs=1,
                        required=True,
                        help="specify user name to login Klocwork Review Server")
    parser.add_argument("--debug",
                        action="store_true",
                        dest="debug",
                        help="specify to generate debug information",
                        default=False)
    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument("--import",
                        action="store",
                        dest="importfile",
                        nargs=1,
                        help="specify input file to import checker configuration")
    output_group.add_argument("--export",
                        action="store",
                        dest="exportfile",
                        nargs=1,
                        help="specify output file to export checker configuration")
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s 0.1')

    args = parser.parse_args()
    
    
    '''
    Set up logger
    '''
    logger = logging.getLogger(__name__)
    logger.stream_log = logging.StreamHandler()
    logger.stream_log.setLevel(logging.DEBUG)
    logger.addHandler(logger.stream_log)
    if (args.debug):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    '''
    Call KW API
    '''
    api = kwapiwrapper.KWAPI(args.review_server_url, args.user[0], logger)
    
    
    if args.importfile:
        infile = open(args.importfile[0], 'r')
        for line in infile:
            elems = line.strip().split(',');
            if len(elems) != 2:
                logger.debug("skipping line %s" % line)
                continue
            checker_name = elems[0]
            enabled = elems[1]
            logger.debug("updating checker setting for %s, checker:%s, enabled:%s" % (args.review_server_project, checker_name, enabled))
            response = api.update_checker_setting(args.review_server_project, checker_name, enabled)
        infile.close()
    
    if args.exportfile:
        outfile = open(args.exportfile[0], 'w')
        response = api.export_checker_config(args.review_server_project)
        for record in response:
            json_checker_setting = json.loads(record)
            outfile.write(json_checker_setting["code"] + "," + str(json_checker_setting["enabled"]) + "\n")
        outfile.close()



    logging.info("DONE")



if __name__ == "__main__" :
    main()