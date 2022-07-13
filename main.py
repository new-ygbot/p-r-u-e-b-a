from pyobigram.utils import sizeof_fmt,get_file_size,createID,nice_time
from pyobigram.client import ObigramClient,inlineQueryResultArticle
from MoodleClient import MoodleClient

from JDatabase import JsonDatabase
import zipfile
import os
import infos
import xdlink
import mediafire
#from megacli.mega import Mega
#import megacli.megafolder as megaf
#import megacli.mega
import datetime
import time
import youtube
import NexCloudClient

from pydownloader.downloader import Downloader
from ProxyCloud import ProxyCloud
import ProxyCloud
import socket
import S5Crypto
import config



def downloadFile(downloader,filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread.getStore('stop'):
            downloader.stop()
        downloadingInfo = infos.createDownloading(filename,totalBits,currentBits,speed,time,tid=thread.id)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def uploadFile(filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        downloadingInfo = infos.createUploading(filename,totalBits,currentBits,speed,time,originalfile)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def processUploadFiles(filename,filesize,files,update,bot,message,thread=None,jdb=None):
    try:
        bot.editMessageText(message,'Subiendo....')
        evidence = None
        fileid = None
        user_info = jdb.get_user(update.message.sender.username)
        cloudtype = user_info['cloudtype']
        proxy = ProxyCloud.parse(user_info['proxy'])
        if cloudtype == 'moodle':
            client = MoodleClient(user_info['moodle_user'],
                                  user_info['moodle_password'],
                                  user_info['moodle_host'],
                                  user_info['moodle_repo_id'],
                                  proxy=proxy)
            loged = client.login()
            itererr = 0
            if loged:
                if user_info['uploadtype'] == 'evidence':
                    evidences = client.getEvidences()
                    evidname = str(filename).split('.')[0]
                    for evid in evidences:
                        if evid['name'] == evidname:
                            evidence = evid
                            break
                    if evidence is None:
                        evidence = client.createEvidence(evidname)

                originalfile = ''
                if len(files)>1:
                    originalfile = filename
                draftlist = []
                for f in files:
                    f_size = get_file_size(f)
                    resp = None
                    iter = 0
                    tokenize = False
                    if user_info['tokenize']!=0:
                       tokenize = True
                    while resp is None:
                          if user_info['uploadtype'] == 'evidence':
                             fileid,resp = client.upload_file(f,evidence,fileid,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'draft':
                             fileid,resp = client.upload_file_draft(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'blog':
                             fileid,resp = client.upload_file_blog(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'calendario':
                             fileid,resp = client.upload_file_calendar(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          iter += 1
                          if iter>=10:
                              break
                    os.unlink(f)
                if user_info['uploadtype'] == 'evidence':
                    try:
                        client.saveEvidence(evidence)
                    except:pass
                return draftlist
            else:
                bot.editMessageText(message,'Error...')
        elif cloudtype == 'cloud':
            tokenize = False
            if user_info['tokenize']!=0:
               tokenize = True
            bot.editMessageText(message,'Subiendo...')
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            remotepath = user_info['dir']
            client = NexCloudClient.NexCloudClient(user,passw,host,proxy=proxy)
            loged = client.login()
            if loged:
               originalfile = ''
               if len(files)>1:
                    originalfile = filename
               filesdata = []
               for f in files:
                   data = client.upload_file(f,path=remotepath,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                   filesdata.append(data)
                   os.unlink(f)
               return filesdata
        return None
    except Exception as ex:
        bot.editMessageText(message,'Error\n' + str(ex))
        return None


def processFile(update,bot,message,file,thread=None,jdb=None):
    file_size = get_file_size(file)
    getUser = jdb.get_user(update.message.sender.username)
    max_file_size = 1024 * 1024 * getUser['zips']
    file_upload_count = 0
    client = None
    findex = 0
    if file_size > max_file_size:
        compresingInfo = infos.createCompresing(file,file_size,max_file_size)
        bot.editMessageText(message,compresingInfo)
        zipname = str(file).split('.')[0] + createID()
        mult_file = zipfile.MultiFile(zipname,max_file_size)
        zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(file)
        zip.close()
        mult_file.close()
        client = processUploadFiles(file,file_size,mult_file.files,update,bot,message,jdb=jdb)
        try:
            os.unlink(file)
        except:pass
        file_upload_count = len(zipfile.files)
    else:
        client = processUploadFiles(file,file_size,[file],update,bot,message,jdb=jdb)
        file_upload_count = 1
        bot.editMessageText(message,'Terminando..')
    bot.editMessageText(message,"Error")    
    evidname = ''
    files = []
    if client:
        if getUser['cloudtype'] == 'moodle':
            if getUser['uploadtype'] == 'evidence':
                try:
                    evidname = str(file).split('.')[0]
                    txtname = evidname + '.txt'
                    evidences = client.getEvidences()
                    for ev in evidences:
                        if ev['name'] == evidname:
                           files = ev['files']
                           break
                        if len(ev['files'])>0:
                           findex+=1
                    client.logout()
                except:pass
            if getUser['uploadtype'] == 'draft' or getUser['uploadtype'] == 'blog' or getUser['uploadtype']=='calendario':
               for draft in client:
                   files.append({'name':draft['file'],'directurl':draft['url']})
        else:
            for data in client:
                files.append({'name':data['name'],'directurl':data['url']})
        bot.deleteMessage(message.chat.id,message.message_id)
        finishInfo = infos.createFinishUploading(file,file_size,max_file_size,file_upload_count,file_upload_count,findex)
        filesInfo = infos.createFileMsg(file,files)
        bot.sendMessage(message.chat.id,finishInfo+'\n'+filesInfo,parse_mode='html')
        if len(files)>0:
            txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
            sendTxt(txtname,files,update,bot)
        try:
            import urllib
            user_info = jdb.get_user(update.message.sender.username)
            cloudtype = user_info['cloudtype']
            proxy = ProxyCloud.parse(user_info['proxy'])
            if cloudtype == 'moodle':
                client = MoodleClient(user_info['moodle_user'],
                                    user_info['moodle_password'],
                                    user_info['moodle_host'],
                                    user_info['moodle_repo_id'],
                                    proxy=proxy)
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            if getUser['uploadtype'] == 'calendar' or getUser['uploadtype'] == 'draft':
                nuevo = []
                #if len(files)>0:
                    #for f in files:
                        #url = urllib.parse.unquote(f['directurl'],encoding='utf-8', errors='replace')
                        #nuevo.append(str(url))
                fi = 0
                for f in files:
                    separator = ''
                    if fi < len(files)-1:
                        separator += '\n'
                    nuevo.append(f['directurl']+separator)
                    fi += 1
                urls = asyncio.run(send_calendar(host,user,passw,nuevo))
                loged = client.login()
                if loged:
                    token = client.userdata
                    modif = token['token']
                    client.logout()
                nuevito = []
                for url in urls:
                    url_signed = (str(sign_url(modif, URL(url))))
                    nuevito.append(url_signed)
                loco = '\n'.join(map(str, nuevito))
                fname = str(txtname)
                with open(fname, "w") as f:
                    f.write(str(loco))
                #fname = str(randint(100000000, 9999999999)) + ".txt"
                bot.sendMessage(message.chat.id,'Link a Calendar')
                bot.sendFile(update.message.chat.id,fname)
            else:
                return
        except:
            bot.sendMessage(message.chat.id,'Error moviendo a calendar')
    else:
        bot.editMessageText(message,'Error'+str(ex))
        return    

def ddl(update,bot,message,url,file_name='',thread=None,jdb=None):
    downloader = Downloader()
    file = downloader.download_url(url,progressfunc=downloadFile,args=(bot,message,thread))
    if not downloader.stoping:
        if file:
            processFile(update,bot,message,file,jdb=jdb)
        else:
            megadl(update,bot,message,url,file_name,thread,jdb=jdb)

def megadl(update,bot,message,megaurl,file_name='',thread=None,jdb=None):
    megadl = megacli.mega.Mega({'verbose': True})
    megadl.login()
    try:
        info = megadl.get_public_url_info(megaurl)
        file_name = info['name']
        megadl.download_url(megaurl,dest_path=None,dest_filename=file_name,progressfunc=downloadFile,args=(bot,message,thread))
        if not megadl.stoping:
            processFile(update,bot,message,file_name,thread=thread)
    except:
        files = megaf.get_files_from_folder(megaurl)
        for f in files:
            file_name = f['name']
            megadl._download_file(f['handle'],f['key'],dest_path=None,dest_filename=file_name,is_public=False,progressfunc=downloadFile,args=(bot,message,thread),f_data=f['data'])
            if not megadl.stoping:
                processFile(update,bot,message,file_name,thread=thread)
        pass
    pass

def sendTxt(name,files,update,bot):
                txt = open(name,'w')
                fi = 0
                for f in files:
                    separator = ''
                    if fi < len(files)-1:
                        separator += '\n'
                    txt.write(f['directurl']+separator)
                    fi += 1
                txt.close()
                bot.sendFile(update.message.chat.id,name)
                os.unlink(name)

def onmessage(update,bot:ObigramClient):
    try:
        thread = bot.this_thread
        username = update.message.sender.username
        tl_admin_user = os.environ.get('tl_admin_user')

        tl_admin_user = config.admin

        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()

        user_info = jdb.get_user(username)

        if username == tl_admin_user or tl_admin_user=='*' or user_info :  # validate user
            if user_info is None:
                if username == tl_admin_user:
                    jdb.create_admin(username)
                else:
                    jdb.create_user(username)
                user_info = jdb.get_user(username)
                jdb.save()
        else:
            msg323= "No tienes acceso"
            bot.sendMessage(update.message.chat.id,msg323)
            return


        msgText = ''
        try: msgText = update.message.text
        except:pass

        # comandos de admin
        if '/adduser' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    jdb.create_user(user)
                    jdb.save()
                    msg = "Usuario @"+user+" tiene acceso"
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'Error en el comando /adduser username')
            else:
                bot.sendMessage(update.message.chat.id,'Acceso Denegado')
            return
        if '/addadmin' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    jdb.create_admin(user)
                    jdb.save()
                    msg = " @"+user+" ahora es Admin del bot "
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'Error en el comando /adduser username')
            else:
                bot.sendMessage(update.message.chat.id,'Acesso Denegado')
            return
        if '/banuser' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    if user == username:
                        bot.sendMessage(update.message.chat.id,'No Se Puede Banear Usted')
                        return
                    jdb.remove(user)
                    jdb.save()
                    msg = '@'+user+' Baneado'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'Error en el comando /banuser username')
            else:
                bot.sendMessage(update.message.chat.id,'Acceso Denegado')
            return
        if '/getdb' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                bot.sendMessage(update.message.chat.id,'Base De Datos')
                bot.sendFile(update.message.chat.id,'database.jdb')
            else:
                bot.sendMessage(update.message.chat.id,'Acceso Denegado')        
            return
        # end

        # comandos de usuario
        if "/status_bot":
            isadmin = jdb.is_admin(username)
            useradmint = jdb.create_user(username)
            try:
                statuss = f"Status del bot:\n\n Admin:"+(isadmin)+separator
                statuss += f"Usuarios con acceso:"+(useradmint)+separator
                bot.sendMessage(update.message.chat.id,statuss)
                return
            except:pass    
        if '/tuto' in msgText:
            tuto = open('tuto.txt','r')
            bot.sendMessage(update.message.chat.id,tuto.read())
            tuto.close()
            return
        if '/info' in msgText:
            getUser = user_info
            if getUser:
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,statInfo)
                return
        if '/zips' in msgText:
            getUser = user_info
            if getUser:
                try:
                   size = int(str(msgText).split(' ')[1])
                   getUser['zips'] = size
                   jdb.save_data_user(username,getUser)
                   jdb.save()
                   msg = 'Zips Cambiados a: '+ sizeof_fmt(size*1024*1024)
                   bot.sendMessage(update.message.chat.id,msg)
                except:
                   bot.sendMessage(update.message.chat.id,'Ponga el tamaño de los zips')
                return
        if '/account' in msgText:
            try:
                account = str(msgText).split(' ',2)[1].split(',')
                user = account[0]
                passw = account[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_user'] = user
                    getUser['moodle_password'] = passw
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,"Usuario y contraseña guardado con existo")
            except:
                bot.sendMessage(update.message.chat.id,'Ponga su usuario separado de la contraseña')
            return
        if '/host' in msgText:
            try:
               if "https" or "http" in msgText: 
                cmd = str(msgText).split(' ',2)
                host = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_host'] = host
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,"Host guardado")
               else: bot.sendMessage(update.message.chat.id,"Host no permitido, Revise bien el url")     
            except:
                bot.sendMessage(update.message.chat.id,'Error al guardar el host')
            return
        if '/repo' in msgText:
            try:
                repoid = msgText.split(" ")[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_repo_id'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,"Su repo ahora es: "+repoid+" ")
            except:
                bot.sendMessage(update.message.chat.id,'Ponga el repo correctamente :)')
            return
        if '/cloud' in msgText:
            try:
               if "cloud" or "moodle" in msgText: 
                cmd = str(msgText).split(' ',2)
                repoid = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['cloudtype'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,"Perfecto el tipo de nube cambiado a "+repoid+"")
               else: bot.sendMessage(update.message.chat.id,"Tipo de nube no permitido")     
            except:
                bot.sendMessage(update.message.chat.id,'Error en el comando /cloud (moodle or cloud)')
            return
        if '/uptype' in msgText:
            try:
               if  "calendar" or "perfil" or "evidence" or "blog" or "draft" in msgText:
                cmd = str(msgText).split(' ',2)
                type = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['uploadtype'] = type
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,"Uptype cambiado a: "+type+"")
               else: bot.sendMessage(update.message.chat.id,"Uptype no permitido")
            except:
                bot.sendMessage(update.message.chat.id,'Error en el comando /uptype (typo de subida)')
            return
        if '/set_proxy' in msgText:
            try:
               if "socks5://" or 123456789 or "." or ":" or "http" in msgText:
                cmd = str(msgText).split(' ',2)
                proxy = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['proxy'] = proxy
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,"Proxy guardado")
               else: bot.sendMessage(update.message.chat.id,"Proxy no permitido, debe llevar lo siguiente : socks5://")           
            except: pass
            return
        if '/del_proxy' in msgText:
            try:
                getUser = user_info
                if getUser:
                    proxy = getUser['proxy']
                    if proxy != '' : 
                        getUser['proxy'] = ''
                        jdb.save_data_user(username,getUser)
                        jdb.save()
                        succes_msg = 'Proxy elimindado'
                        bot.sendMessage(update.message.chat.id,succes_msg)
                    else : bot.sendMessage(update.message.chat.id,'No tienes proxy')
            except:
                if user_info:
                    proxy = getUser['proxy']
                    if proxy != '' : 
                        getUser['proxy'] = ''
                        jdb.save_data_user(username,getUser)
                        jdb.save()
                        succes_msg = 'Proxy eliminado'
                        bot.sendMessage(update.message.chat.id,succes_msg)
                    else : bot.sendMessage(update.message.chat.id,'No posees proxy')
            return            
        if '/dir' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['dir'] = repoid + '/'
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'Error, ponga su carpeta')
            return
        if '/cancel_' in msgText:
            try:
                cmd = str(msgText).split('_',2)
                tid = cmd[1]
                tcancel = bot.threads[tid]
                msg = tcancel.getStore('msg')
                tcancel.store('stop',True)
                time.sleep(3)
                bot.editMessageText(msg,'Tarea Cancelada')
            except Exception as ex:
                print(str(ex))
            return
        #end

        message = bot.sendMessage(update.message.chat.id,'Leyendo datos....')

        thread.store('msg',message)
        if '/login' in msgText:
             Msg1 = "Conectando..."
             getUser = user_info
             if getUser:
                 user = getUser['moodle_user']
                 passw = getUser['moodle_password']
                 host = getUser['moodle_host']
                 proxy = getUser['proxy']
                 if user and passw and host != '':
                        info= MoodleClient(getUser['moodle_user'],
                                           getUser['moodle_password'],
                                           getUser['moodle_host'],
                                           proxy=proxy)
                        logins = client.login()
                        if logins:
                                bot.editMessageText(Msg1,"Conexion Ready :D")  
                        else: bot.editMessageText(Msg1,"Error al conectar")                         
                 else: bot.editMessageText(Msg1,"No ha puesto sus credenciales")
        if '/start' in msgText:
            start_msg = '#Inicio de sesion correcto\n\nBienvenido @'+username+' al bot de descargas gratis.\n'
            bot.editMessageText(message,start_msg)
            return
        if '/token' in msgText:
            message2 = bot.editMessageText(message,'Obteniendo Token...')
            try:
                proxy = ProxyCloud.parse(user_info['proxy'])
                client = MoodleClient(user_info['moodle_user'],
                                      user_info['moodle_password'],
                                      user_info['moodle_host'],
                                      user_info['moodle_repo_id'],proxy=proxy)
                loged = client.login()
                if loged:
                    token = client.userdata
                    modif = token['token']
                    bot.editMessageText(message2,'Su Token es: '+modif)
                    client.logout()
                else:
                    bot.editMessageText(message2,'La Moodle '+client.path+' No tiene Token')
            except Exception as ex:
                bot.editMessageText(message2,'La Moodle '+client.path+' No tiene Token o revise la Cuenta')
        elif '/files' == msgText and user_info['cloudtype']=='moodle':
             proxy = ProxyCloud.parse(user_info['proxy'])
             client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
             loged = client.login()
             if loged:
                 files = client.getEvidences()
                 filesInfo = infos.createFilesMsg(files)
                 bot.editMessageText(message,filesInfo)
                 client.logout()
             else:
                bot.editMessageText(message,'ERROR. Revise la nube')
             return
        elif '/txt_' in msgText and user_info['cloudtype']=='moodle':
            findex = str(msgText).split('_')[1]
            findex = int(findex)
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
            loged = client.login()
            if loged:
                 evidences = client.getEvidences()
                 evindex = evidences[findex]
                 txtname = evindex['name']+'.txt'
                 sendTxt(txtname,evindex['files'],update,bot)
                 client.logout()
                 bot.editMessageText(message,'TxT Aqui')
            else:
                bot.editMessageText(message,'ERROR. Revise la nube ')
            pass
        elif '/del_' in msgText and user_info['cloudtype']=='moodle':
            findex = int(str(msgText).split('_')[1])
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],
                                   proxy=proxy)
            loged = client.login()
            if loged:
                evfile = client.getEvidences()[findex]
                client.deleteEvidence(evfile)
                client.logout()
                bot.editMessageText(message,'🗑 Archivo Borrado ...')
            else:
                bot.editMessageText(message,'ERROR. Revise la nube')
        if '/del_files' in msgText and user_info['cloudtype']=='moodle':
            contador = 0
            eliminados = 0
            bot.editMessageText(message,'Eliminando los 50 Primero Elementos...')
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                user_info['moodle_password'],
                                user_info['moodle_host'],
                                user_info['moodle_repo_id'],
                                proxy=proxy)
            loged = client.login()
            prueba = client.getEvidences()
            if len(prueba) == 0:
                bot.sendMessage(update.message.chat.id,'La Moodle está vacia')
                return 
            try:
                for contador in range(50):
                    proxy = ProxyCloud.parse(user_info['proxy'])
                    client = MoodleClient(user_info['moodle_user'],
                                    user_info['moodle_password'],
                                    user_info['moodle_host'],
                                    user_info['moodle_repo_id'],
                                    proxy=proxy)
                    loged = client.login()
                    if loged:               
                            evfile = client.getEvidences()[0]
                            client.deleteEvidence(evfile)
                            eliminados += 1
                            bot.sendMessage(update.message.chat.id,'Archivo ' +str(eliminados)+' Eliminado')                            
                    else:
                        bot.sendMessage(update.message.chat.id,'ERROR. Revise la nube')
                bot.sendMessage(update.message.chat.id,'Se eliminaron los archivos en un rango de 50')
            except:
                bot.sendMessage(update.message.chat.id,'No se pudieron eliminar 50 elementos solo se eliminaron '+str(eliminados))
        elif '/delete' in msgText:
           try: 
            enlace = msgText.split('/delete')[-1]
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],
                                   proxy=proxy)
            loged= client.login()
            if loged:
                #update.message.chat.id
                deleted = client.delete(enlace)

                bot.sendMessage(update.message.chat.id, "Archivo eliminado con exito...")
            else: bot.sendMessage(update.message.chat.i, "No se pudo loguear")            
           except: bot.sendMessage(update.message.chat.id, "No se pudo eliminar el archivo")       
        elif '/download' in msgText:
           try: 
            url = msgText.split(" ")[1]
            ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb)
           except: bot.editMessageText(message,"Error al descargar el archvivo")
        else:
            bot.editMessageText(message,'Comando erroneo')
    except Exception as ex:
           print(str(ex))


def main():
    bot_token = os.environ.get('bot_token')

    bot_token = config.bot_token

    bot = ObigramClient(bot_token)
    bot.onMessage(onmessage)
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except:
        main()
