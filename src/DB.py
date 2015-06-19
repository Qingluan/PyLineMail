from mongoHelper import Mongo
import re
import getpass

def test_db():
    print("load module ok ")
    try :
        
        import mongoHelper
        print("load db module ok ")
    except :
        print("not installed mongoHelper , this can install by my github/Qingluan ")

class _DB(object):
    oper_map = {
        '=' : '$eq',
        '>' : '$gt',
        '<' : '$lt',
    }

    
    user_setting_template = {
        'HASH': 'SHA-1',

        'client': 'smtp.%s.com',
        'encoders': {
            'base64': 'b64encode',
            },
        'port': 465,
        'server': {
                "type":"pop3",
                "connect":"xxx this will be eval",
                "address":"pop.%s.com",
            },
        'address': '%s@%s.%s',
        "pass":"xxx",

    }


    
    def user_setting(self):
        def _set_one_item(key):

            item = raw_input(key+" :")
            return item

        nickname = raw_input("nickname >")

        user_setting_template = self.user_setting_template
        print user_setting_template
        for k in ["client","address","pass"] :
            # setattr(user_setting_template, k, _set_one_item(k))
            # ite =_set_one_item(k)
            # print ite
            user_setting_template[k] = _set_one_item(k)
        

        for k in ["type","address",] :
            if k== "type":
                print ("(input receive server type)")
            user_setting_template["server"][ k] =  _set_one_item(k)
            # _DB.user_setting["server"][k] = _set_one_item(k)
        
        if self.mongo.find("usage",**{
                "nickname":nickname,
            }):
            
            self.mongo.update("usage",{
                "nickname":nickname,
                "setting":user_setting_template,
                },**{
                "nickname":nickname,
                })
        else:
            self.mongo.insert("usage",**{
                "nickname":nickname,
                "setting":user_setting_template,
                })



    def __init__(self,DB):
        self.mongo = Mongo(DB)     

    def login(self,nickname):
        print "login .."
        print nickname
        pass_t = getpass.getpass()
        if self.mongo.find_one("login"):
            print "you have logined !!"
            exit(0)

        if self.mongo.find_one("usage",**{
                "nickname":nickname,
                "setting.pass":pass_t,
            }):
            self.mongo.insert("login",**{
                    "nickname":nickname,
                })
            print "login successful !"
        else:
            print ("password is error : login failed ")
            exit(0)

    def load_setting(self,user=None):
        # print("load .. config from db")
        nick_name = self.mongo.find_one("login")["nickname"]
        if user:
            nick_name = user
            
        if not nick_name:
            print ("not select a user to login in long time,just use \'--login\' argument ")
            exit(0)
        return self.mongo.find_one("usage",**{
                "nickname":nick_name,
            })


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
    decs = """
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

    def delete_user(self,user):
        return self.mongo.remove("user",**{
                "user":user,
            })

    def insert_mail(self,mail):
        log ={}
        for key in mail.keys():
            content = mail[key]
            if key == "To":
                ty = re.findall(r'@(\w+?)\.', content)[0]
                full = content
                content = {
                    "type" : ty,
                    "full":full,
                }
            log[key] = content
        log["payload"] = mail.get_payload()

        self.mongo.insert("mail",**log)

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

