#!/usr/bin/env python
# -*- coding: gbk -*-   

import smtplib, mimetypes  
from email.mime.text import MIMEText  
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart  
import email
import sys,os
import re

import rsa
import argparse
from base64 import b64encode



## this mongodbHelper is written by Qingluan ,you can download and install in github
from mongoHelper import Mongo


def get_arguments():
    desc = """
    this is a email send client , event can signature 
    written by qingluan
    """

    parser = argparse.ArgumentParser(usage="mail client",description=desc)

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
    parser.add_argument("-d","--delete",default=None,help="this is sub argument of -i ,for search/insert user ,\
        \nexample : -s -d \"[user,mail] qingluan  \" ")
    parser.add_argument("-a","--argv",default=None,help="this is sub argument of -s ,for search/insert user ,\
            \nexample : \
         email  -s -a \"[user,mail] [time.day,time.mon,time.week,time.year] [=,>,<] 100\" \
         \nemail -s -a \"[mail] [to.f] xxx@gmail.com \n\
         email -s -a \"[mail]  [to.type|to.user]  [gmail,qq....]  ")

    return parser.parse_args()

class _DB(object):
    oper_map = {
        '=' : '$eq',
        '>' : '$gt',
        '<' : '$lt',
    }

    


    def __init__(self,DB):
        self.mongo = Mongo(DB)     

    def load_setting(self):
        # print("load .. config from db")
        return self.mongo.find_one("usage")

    def check_argv(self,argv):
        argv = argv.strip()
        args = argv.split()
        try :
            i = int(args[-1] )
            args[-1] = i
            return args
        except ValueError:
            return args


    def get_db_dict(self,argv):
        
        self.args = self.check_argv(argv)

        self.num = len(self.args)
        print(self.num)
        self.document = self.args[0]

        if self.num == 1:
            return self.document,None

        if self.args[-2] in Searcher.oper_map:
            self.args[-2] = Searcher.oper_map[self.args[-2]]



        args = self.args[1:]
        if self.num % 2== 1 :
            return self.document,dict([ (args[i],args[i+1]) for i in range(0,len(args),2) ])
        else:

            # this is very clever function , i must  favor myself
            args.reverse()
            return self.document,reduce(lambda x,y : {y : x} , args)  


class Inserter(_DB):
    """
        mail log:
            {
                "to":{
                    "full":"xxx@gmail.com",
                    "type":"gmail",
                    "user":"some",
                    },
                "content":"xxxx"
                "if_signature":boolean,
                "attach":xxxx,

            }
        user log:
        {
            "user":'xxx',
            "to" : "xxxx@gmail.com",
            "contact":{
                ...
            }
        }

    """
    def insert(self,argv):
        docu,db_str = self.get_db_dict(argv)
        return self.mongo.insert(docu,**db_str)

    def delete(self,argv):
        docu,db_str = self.get_db_dict(argv)
        return self.mongo.remove(docu,**db_str)

    def insert_log(self,user,to_address,subject,content,attach=False,if_sign=False):
        # print (to_address)
        mail_type = re.findall(r'@(\w+?)\.', to_address)[0]

        log = {
                "to":{
                    "full":to_address,
                    "type":mail_type,
                    "user":user,
                    },
                "subject":subject,
                "content":content,
                "if_sign":if_sign,
                "attach":attach,

            }

        self.mongo.insert("mail",**log)
    
    def insert_user(self,user,address):
        U = {
                "user":user,
                "to" : address,
            }

        self.mongo.insert("user",**U)

        


class Searcher(_DB):

    def find(self,argv):
        docu,db_str = self.get_db_dict(argv)
        print docu,db_str
        if db_str:
            return self.mongo.find(docu,**db_str)
        else:
            return self.mongo.find(docu)

    def find_user(self,user):
        return self.mongo.find("user",**{
            "user":user,
            })



class Contact:
    
    Contact = {
    #<contact>
        'mao' : 'maoxinhorizon@gmail.com',
        'tong': 'wickzt@gmail.com',
        'meng': 'mengwei607@gmail.com',
        'zhen': '764825975@qq.com',

    #<contact>
    }   
    @staticmethod
    def get(key):
        return Contact.Contact[key]



class MailServer:
    
    def __load_setting__(self,setting):
        MailServer.setting = setting
        self.searcher = Searcher("email")
        for key in MailServer.setting["encoders"]:
            method_str = MailServer.setting["encoders"][key] 
            MailServer.setting["encoders"][key] = eval(method_str)


    def __init__(self,pass_t,setting):
        print ("load mail setting ")
        
        self.__load_setting__(setting)
        print ("Connecting ...")

        self.smtp = smtplib.SMTP()
        # self.smtp.set_debuglevel(1)

        try:
            self.smtp.connect(MailServer.setting['server'])
        except :
            print ("\rConnecting error **********")
        # self.smtp.ehlo()
        # self.smtp.starttls()
        
        try:
            print ("logging....")
            print ("user : ",MailServer.setting['user'])
            self.smtp.login(MailServer.setting['user'],pass_t)
            print ("login ok!!!******************")
            # self.smtp.ehlo()
        except :
            print ("login ...error  *************")
        # print self.smtp.getreply()

    def check_address(self,address):
        if "@" not in address:
            return self.searcher.find_user(address)[0]["to"]
        return address
 
    def load(self,to_add,plain_text,summary='subject',attach="",if_sign=False):
        plain_text = str(plain_text)
        # print type("stomsd")
        self.to_add = self.check_address(to_add)

        self.msg = MIMEMultipart()
        self.msg['From'] = MailServer.setting['user']
        self.msg['To'] = to_add
        self.msg['Subject'] = summary
        self.msg.set_boundary( "="*17+" QingLuan "+"="*17)
        T = MIMEText(plain_text)
        # print(self.msg)

        self.msg.attach(T)
        # self.msg.set_charset('gb2312')
        # print (text)
        if attach:
            att = self.add_attachmen(attach)
            self.msg.attach(att)
        IN.insert_log(MailServer.setting["user"],self.to_add,summary,plain_text,attach=attach,if_sign=if_sign)
    def add_attachmen(self,attach):
        
            ctype,encoding = mimetypes.guess_type(attach)
            if ctype is None or encoding is not None:
                ctype='application/octet-stream'
            maintype,subtype = ctype.split('/',1)
            print (maintype ,subtype)

            att=MIMEImage(open(attach, 'rb').read(),subtype)
            print (ctype,encoding)
            Content_dis = 'attachmemt;filename="%s"' %attach
            print (Content_dis)
            att["Content-Disposition"] = Content_dis 
            return att
            
        # self.smtp.sendmail(MailServer.setting['user'],to_add,self.msg.as_string())
    
    def send(self,log=False):
        try:
            self.smtp.sendmail(MailServer.setting['user'],self.to_add,self.msg.as_string())
            print ("send  email ok")
            if log:
                print (self.msg)

        except smtplib.SMTPSenderRefused :
            print ("Error Pass check again\n")
            exit(0)
        # self.smtp.send("\nfrom Dr.%s"% MailServer.setting['user'])
        # self.smtp.getreply()
        # self.close()
        
        # self.smtp.quit()
    def gen_content_mime(self,content,types,transfer="base64",charset="utf-8"):
            encoder = mail.setting["encoders"][transfer]
            text = MIMEText(encoder(content))
            
            text.set_type(types)
            # text.add_header("filename", "signed.p1s")
            text.add_header('content-disposition', 'attachment', filename='signed.p1s')
            text.add_header("name", "signed.p1s")
            text.replace_header("Content-Transfer-Encoding",transfer)
            text.set_charset(charset)

            return text


    def signature(self,content,private_key_file):
        """
            signature the content
        """

            # get private key and signature
        private_key = None
        with open(private_key_file,"r") as fp:
            text = fp.read()
            private_key = rsa.PrivateKey.load_pkcs1(text)

        signatured_content = rsa.sign(content,private_key,self.setting["HASH"])
        # set preamble content 
        
        # self.msg.preamble = MIMEText(content)
        self.msg.preamble = "this is from Qingluan'client .. written by Py"
        # self.msg.add_header("Content-type","text/plain")
        # set payload 
        # print(signatured_content)

        # with open("signed.p1s","wb") as fp:
        #     fp.write(signatured_content)
        
        # signatured_payload = self.add_attachmen("signed.p1s") # self.gen_content_mime(signatured_content,"application/python2.7-rsa-sign")
        signatured_payload = self.gen_content_mime(signatured_content,"application/python2.7-rsa-sign")
        self.msg.attach(signatured_payload)

        # change main mime type
        self.msg.set_type("multipart/signed")
        self.msg.set_param("micalg",self.setting["HASH"])
        return signatured_content

    def get_content(self,content):
            # check content is file or content 
        text = content
        if os.path.exists(content):
            with open(content) as fp:
                text = fp.read().encode("utf8")

        return text
                
def Log(d):
    for i in d:
        print "%-10s : \t\t%+40s"%(i,d[i])


if __name__ == "__main__":
    ############## test ####################
    args = get_arguments()
    IN = Inserter("email")


    SETTING =  IN.load_setting()

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
            [Log(i) for i in S.find_user(args.user) ]
            exit(0)
        print args.argv
        res = S.find(args.argv)

        [ Log(i) for i in res]
        exit(0)


    import getpass


    print "pass > ",
    pass_t = getpass.getpass()


    mail = None
    if args.contact:
        mail = MailServer(pass_t,setting=SETTING)
        text_or_file_path = args.text
        content = mail.get_content(text_or_file_path)
        if_si = False
        if args.signature :
            if_si = True
        mail.load(args.contact,content,summary=args.subject,attach=args.attachment,if_sign=if_si)

        if args.signature:
            text = mail.signature(content,args.signature)

            
            
        mail.send(log=True)
    