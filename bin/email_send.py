#!/usr/bin/env python
# -*- coding: gbk -*-   


import sys
import argparse

sys.path += ["../src"]
sys.path += ["/usr/local/lib/python2.7/site-packages/PyLineMail/src"]

from Mail import MailClient
from Mail import MailServer
from DB import Inserter,Searcher
from DB import test_db
from Mail import test_mail

## this mongodbHelper is written by Qingluan ,you can download and install in github



def get_arguments():
    desc = """
    this is a email send client , event can signature 
    written by qingluan
    """

    parser = argparse.ArgumentParser(usage="mail client",description=desc)

    parser.add_argument("-n",'--account_setting',default=None,action="store_true",help="setting user account")
    parser.add_argument("-l",'--login',default=None,help="login user and to register it to local db")

    parser.add_argument("-c","--contact",default=None,help="contact include mail address")
    parser.add_argument("-m","--subject",default="No Subject",help="subject of mail ")
    parser.add_argument("-t","--text",default="No Content",help="content can use file name")

    parser.add_argument("-S","--signature",default=None,help="signature private key file ")

    parser.add_argument("-A","--attachment",default=None,help="attachment file specified ")
    parser.add_argument("-s","--search",action="store_true",default=False,help="search mode turn on,\
        will insert some data to mongo db")
    parser.add_argument("-i","--insert",action="store_true",default=False,help="insert db mode turn on\
        will search something from mongo db")
    parser.add_argument("-u","--user",default=None,help="this is sub argument of -s/-i ,for search/insert user ,\
        \nexample : -s/-i -u \" qingluan  xxx@gmail.com\" ")
    parser.add_argument("-d","--delete",action="store_true",default=False,help="this is sub argument of -i ,for search/insert user ,\
        \nexample : -s -d \"[user,mail] qingluan  \" ")
    parser.add_argument("-a","--argv",default=None,help="this is sub argument of -s ,for search/insert user ,\
            \nexample : \
         email  -s -a \"[user,mail] [time.day,time.mon,time.week,time.year] [=,>,<] 100\" \
         \nemail -s -a \"[mail] [to.f] xxx@gmail.com \n\
         email -s -a \"[mail]  [to.type|to.user]  [gmail,qq....]  ")
    parser.add_argument("-f",'--format',default=False,action="store_true",help="see the format in mongo DB")

    # mail receiving function 
    parser.add_argument("-r",'--receive',default=None,help="receive from mail by use -r xxx to choose account")

    parser.add_argument("--test",default=False,action="store_true",help="this is for test if ok for  installation  ")

    return parser.parse_args()



                
def Log(d):
    if not d:
        print("Not found ")
        return 

    def _Log(l):
        for i in l:
            print "%-10s : \t\t%+40s"%(i,l[i])
    

    [_Log(i) for i in d ]


if __name__ == "__main__":
    ############## test ####################
    args = get_arguments()
    IN = Inserter("email")

    if args.test :
        test_mail()
        test_db()

    if args.account_setting:

        IN.user_setting()
        exit(0)

    if args.login:
        IN.login(args.login)

    SETTING =  IN.load_setting()["setting"]

    if args.format:
        print Inserter.decs
        exit(0)

    if args.receive:
        mail_received = MailServer(args.receive)
        mail_received.get_msgs()
        print "email have received successful!!"
        exit(0)

    if args.insert:
        if args.user:
            if (len(args.user.split())) == 2:
                res = args.user.strip().split()
                print res
                IN.insert_user(*res)
            else:
                print args
        exit(0)
    elif args.search:
        del IN
        S = Searcher("email")
        if args.user:
            Log(S.find_user(args.user))
            exit(0)
        print args.argv
        res = S.find(args.argv)

        Log(res)
        exit(0)
    elif args.delete :
        if args.user:
            IN.delete_user(args.user)
        else:
            IN.delete(args.argv)
        exit(0)


    import getpass


    print "pass > ",
    pass_t = getpass.getpass()


    mail = None
    if args.contact:
        mail = MailClient(pass_t,setting=SETTING)
        text_or_file_path = args.text
        content = mail.get_content(text_or_file_path)
        if_si = False
        if args.signature :
            if_si = True
        mail.load(args.contact,content,summary=args.subject,attach=args.attachment,if_sign=if_si)

        if args.signature:
            text = mail.signature(content,args.signature)

            
            
        mail.send(log=True)
    
