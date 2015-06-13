
import smtplib, mimetypes  
from email.mime.text import MIMEText  
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart  
from email import quoprimime  as qmime

import email
from base64 import b64decode
from base64 import b64encode
import re
import os
import rsa
import sys
import poplib
from email import parser
import quopri
from DB import Searcher,Inserter

import poplib
import imaplib

# from email_send import Log

def trans_quote(string):
    # print string
    # real_string = re.findall(r'(\=\?.+\?\=)',string)
    # real_string =qmime.decode(string).decode("gbk")
    # print real_string
    # print type(string)
    string = string.strip()
    if len(re.findall(r'=..',string)) <4:
        # if len(string) % 4== 0:
        try:
            res =  b64decode(string)
        except TypeError:
            # print "|"+string+"|"
            res = string
        finally:
            return res
    else:
     # qmime.body_quopri_check(string):
    # print "bad"
        return qmime.decode(string)
    # return string


def utf(string):
    return string.decode("utf8")

def gbk(string):
    return string.decode("gbk")


def Log(d):
    if not d:
        print("Not found ")
        return 

    def _Log(l):
        for i in l:
            print "%-10s : \t\t%+40s"%(i,l[i])
    
    if isinstance(d, list):
        [_Log(i) for i in d ]
    else:
        _Log(d)
def RLog(line):
    sys.stdout.write(line+"\r")
    sys.stdout.flush()

class BaseMail(object):

    def __load_setting__(self,setting=None,user=None):
        BaseMail.setting = setting
        
        self.inserter = Inserter("email")
        if setting:
            for key in BaseMail.setting["encoders"]:
                method_str = BaseMail.setting["encoders"][key] 
                BaseMail.setting["encoders"][key] = eval(method_str)
        # if user:
            # BaseMail.setting = setting["receive"][user]
        
            BaseMail.setting["nickname"] = self.inserter.mongo.find_one("login")["nickname"]
        if user:
            BaseMail.setting = self.inserter.load_setting(user)["setting"]
            # Log(BaseMail.setting)
            BaseMail.setting["nickname"] = user
class MailServer(BaseMail):
    connect = {
        "pop3":poplib.POP3_SSL,
        "imap":imaplib.IMAP4_SSL,
    }
    
    payload_decode = {
        "base64":b64decode,
        "quoted-printable":trans_quote,
    }

    charset_decodes = {
        "ut":utf,
        "gb":gbk,
    }

    def __init__(self,user):
        print ("load mail setting ")
        
        self.__load_setting__(user=user)
        print ("Connecting ...")

        
        # self.smtp.set_debuglevel(1)
        con_type = None
        try:
            con_type = BaseMail.setting['server']["type"]
            print con_type
            connecter = MailServer.connect[con_type]

            self.conn = connecter(BaseMail.setting['server']['address'])
            
            self.inserter = Inserter("email")
            # parser = parser.Parser()
            self.mail_parse = email.message_from_string

        except  Exception ,e:
            print e
            print ("\rConnecting error **********")
        # self.smtp.ehlo()
        # self.smtp.starttls()
        
        try:

            print ("logging....")
            print ("user : ",BaseMail.setting["server"]['address'])
            if con_type == "pop3":
                self.conn.user(BaseMail.setting["address"])
                self.conn.pass_(BaseMail.setting["pass"])
                self.raw_mail = lambda x:"\n".join(self.conn.retr(x[0])[1])
            elif con_type == "imap":
                self.conn.login(BaseMail.setting["address"],BaseMail.setting["pass"])
                self.select("inbox")
            print ("login ok!!!******************")
            # self.smtp.ehlo()
        except Exception,e:
            # e.print_trac
            print ("login ...error  *************")
            print (e)
            print BaseMail.setting
            # exit(0)

    def get_msgs(self):
        def _id_len(id):
            for i in self.list_info:
                if i[0] == id:
                    return i[1]
            return -1
        def _get_id_gen(id_index):
            for i in id_index:
                yield i[0]

        def run_count(*args,**kargs):
            """
            for display degree
            """
            RLog("%-4d/%4d  mail_id :%4s  len : %+8s"%(self.count_id,self.len,self.now_id,self.now_id_len))
            try:
                self.now_id =  self.now_id_gener.next()
            except StopIteration,e:
                print ()
            self.count_id += 1
            self.now_id_len = _id_len(self.now_id)
            return run_count.fun(*args,**kargs)

        def run_map(func,*args):
            """
                extend map 
            """
            run_count.fun = func
            res = map(run_count ,*args)
            self.count_id = 0
            self.now_id_gener = _get_id_gen(self.list_info)
            self.now_id = self.now_id_gener.next()
            self.now_id_len = _id_len(self.now_id)
            return res


        res ,ids,len_ids =  self.conn.list()
        self.list_info = [ m.split() for  m in ids]
        self.now_id_gener = _get_id_gen(self.list_info)
        self.count_id = 0
        self.now_id = self.now_id_gener.next()
        self.now_id_len = _id_len(self.now_id)
        self.len = len(self.list_info)

        # par msg
        RLog("start load raw mail ...")
        raw_mails = run_map(self.raw_mail,self.list_info)
        print("start load raw mail ... ok")


        #parmail
        RLog("start parse raw mail ...")
        msgs = run_map(self.mail_parse ,raw_mails)
        print("start parse raw mail ... ok")
        # print type(msgs[-1])

        RLog("start parse really  mail to in MIME type ...")
        self.msgs = run_map(self.par_payload,msgs)
        print("start parse really  mail to in MIME type ... ok")

        print (self.msgs[-1])
        RLog("start save mail to in mongo ...")
        run_map(self.save_msg, self.msgs)
        print("start save mail to in mongo ... ok")


    def save_msg(self,mail):
        self.inserter.insert_mail(mail)


    def p_mail(self,mail):
        for key in ["Subject","Sender","From","To"]:
            mail = self.decode(mail,key)
        self.decode()
        return mail

    def get_real_quote(self,item):
        return re.findall(r'(\=\?.+\?\=)',item)[0]

    def par_payload(self,mail):
        # print mail
        # if  not isinstance(payload, list):
        # try:
            if  mail.get_content_maintype() == "text":
                decode_type =  mail["Content-Transfer-Encoding"]
                for i in ["To","From","Subject"]:
                    self.decode(mail,key=i,decode_type=decode_type)
                return self.decode(mail,decode_type=decode_type)
            
            elif mail.get_content_maintype() == "multipart":
                for sub_payload in mail.get_payload():
                    self.par_payload(sub_payload)
                    # print decoded_sub
                    # mail.
        # except Exception,e:
            # print e
            # print mail
            # exit(0)

    def decode(self,mail,key=None,decode_type="base64"):
        charseter = MailServer.charset_decodes [mail.get_content_charset().lower()[:2]]
        tr_decode = None
        if decode_type:
            tr_decode = MailServer.payload_decode[decode_type]
            if key:

                val = mail[key]
                if not val:
                    # print val
                    pass

                    # mail.replace_header(key,"no "+key)    
                else:
                    # print val

                    try:
                        tm_val = tr_decode(val)
                        try:

                            mail.replace_header(key,charseter(tm_val ))
                        except UnicodeDecodeError:
                            print mail.get_content_charset(),mail["Content-Transfer-Encoding"],tr_decode
                            # print mail
                            mail.replace_header(key,str(tm_val ))
                        # print tm_val.decode("gbk")
                    except TypeError,e:
                        # print e
                        # print "******"+val
                        print "type error ,type to fix .. "
                        mail.replace_header(key,charseter(val ))

                        # exit(0)
                    # finally:
                        # print mail[key]
                    # print val,mail["Content-Transfer-Encoding"]
                    
                    # print mail[key]
            else:
                payload = mail.get_payload()
                # print payload
                md_payload = tr_decode(payload)
                # print md_payload,tr_decode
                payload = charseter(md_payload)
                # print payload
                    # print payload
                mail.set_payload(payload)
        else:
            if key:
                # if not val:
                    # mail.replace_header(key,"no "+key)    
                # else:
                    # print val
                try:
                    val = mail[key]
                    mail.replace_header(key,charseter(val))
                except :
                    pass
            else:

                payload = mail.get_payload()
                payload = charseter(payload)
                # print payload
                    # print payload
                mail.set_payload(payload)
        # print mail
        return mail
            
    # def decode(self,mail,key=None,decode_type="base64"):

    #     decoder = None
    #     r_q = lambda  x: re.findall(r'(\=\?.+\?\=)',x)[0]

    #     if decode_type:
    #         print decode_type
    #         decoder = MailServer.payload_decode[decode_type]
    #         # print decoder
    #     try:  

    #         if mail.get_content_charset().lower().startswith ("gb")  :
    #             temp_v = re.findall(r'(\=\?.+\?\=)',mail[key])[0]
    #             print temp_v
    #             if key:
    #                 if decoder:
    #                     vl = mail[key]
    #                     if decode_type == "quoted-printable":
    #                         vl = r_q(mail[key])
    #                         print vl
    #                     some_vl = decoder(vl).decode("gbk")
    #                     print some_vl
    #                     mail.replace_header (key ,some_vl ) 
    #                 else:
    #                     mail.replace_header(key,mail[key].decode("gbk"))
    #                 # print MailServer.payload_decode[decode_type]
    #                 # print decode_type,decoder(mail[key]).decode("gbk")
    #                 # print mail[key]
    #             else:
    #                 # print "no key",key

    #                 payload = mail.get_payload()
    #                 payload = decoder(payload).decode("gbk")
    #                 # print payload
    #                 mail.set_payload(payload)
    #         else:
    #             if key:
    #                 # mail[key] = decoder(mail[key]).decode("utf8")
    #                 # print mail[key]
    #                 # temp_v = self.get_real_quote( mail[key])
    #                 # print temp_v ,"end"
    #                 if decoder:
    #                     vl = mail[key]
    #                     if decode_type == "quoted-printable":
    #                         vl = self.get_real_quote(mail[key])
                        
    #                     mail.replace_header (key ,decoder(vl).decode("utf8") )

    #                 else:

    #                     mail.replace_header(key,mail[key].decode("utf8"))
                    
    #             else:
    #                 # print "no key",key
    #                 payload = mail.get_payload()
    #                 payload = decoder(payload).decode("utf8")
    #                 mail.set_payload(payload)
    #         # print "From" ,mail["From"]
    #         # print "To",mail["To"]
    #         # print "Subject",mail["Subject"]
    #     except UnicodeDecodeError,e:
    #         print e,"+++",temp_v,key
    #         # print b64decode(temp_v).decode("utf8")

    #         print mail.get_content_maintype(),mail["Content-Transfer-Encoding"],mail.get_content_charset()
    #         print decoder(mail[key]).decode("utf8")
            
    #         exit(0)
    #     finally:
    #         # print mail.get_content_charset()
    #         # print mail

    #         return mail


class MailClient(BaseMail):
    


    def __init__(self,pass_t,setting):
        print ("load mail setting ")
        
        self.__load_setting__(setting)
        print ("Connecting ...")

        self.smtp = smtplib.SMTP()
        # self.smtp.set_debuglevel(1)

        try:
            self.smtp.connect(BaseMail.setting['client'])
        except :
            print ("\rConnecting error **********")
        # self.smtp.ehlo()
        # self.smtp.starttls()
        
        try:
            print ("logging....")
            print ("address : ",BaseMail.setting['address'])
            self.smtp.login(BaseMail.setting['address'],pass_t)
            print ("login ok!!!******************")
            # self.smtp.ehlo()
        except :
            print ("login ...error  *************")
        # print self.smtp.getreply()

    def check_address(self,address):
        if "@" not in address:
            self.searcher = Searcher("email")
            return self.searcher.find_user(address)[0]["to"]
        return address
 
    def load(self,to_add,plain_text,summary='subject',attach="",if_sign=False):
        plain_text = str(plain_text)
        # print type("stomsd")
        self.to_add = self.check_address(to_add)

        self.msg = MIMEMultipart()
        self.msg['From'] = BaseMail.setting['address']
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
        try:
            self.inserter.insert_log(BaseMail.setting["nickname"],self.to_add,summary,plain_text,attach=attach,if_sign=if_sign)
        except Exception ,e:
            print e
            print BaseMail.setting
            exit(0)

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
            
        # self.smtp.sendmail(BaseMail.setting['user'],to_add,self.msg.as_string())
    
    def send(self,log=False):
        try:
            self.smtp.sendmail(BaseMail.setting['address'],self.to_add,self.msg.as_string())
            print ("send  email ok")
            if log:
                print (self.msg)

        except smtplib.SMTPSenderRefused :
            print ("Error Pass check again\n")
            exit(0)
        # self.smtp.send("\nfrom Dr.%s"% BaseMail.setting['user'])
        # self.smtp.getreply()
        # self.close()
        
        # self.smtp.quit()
    def gen_content_mime(self,content,types,transfer="base64",charset="utf-8"):
            encoder = BaseMail.setting["encoders"][transfer]
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