from cProfile import run
import pstats
from pyobigram.utils import sizeof_fmt,get_file_size,createID,nice_time
from pyobigram.client import ObigramClient,inlineQueryResultArticle
from pyobigram.client import inlineKeyboardMarkup,inlineKeyboardMarkupArray,inlineKeyboardButton

from JDatabase import JsonDatabase
import shortener
import zipfile
import os
import infos
import xdlink
import mediafire
import datetime
import time
import youtube
import NexCloudClient
from pydownloader.downloader import Downloader
from ProxyCloud import ProxyCloud
import ProxyCloud
import socket
import tlmedia
import S5Crypto
import asyncio
import aiohttp
from yarl import URL
import re
import random
from draft_to_calendar import Draft2Calendar
import moodlews
import moodle_client
from moodle_client import MoodleClient
import S5Crypto
import config


group_id = config.groupid


def sign_url(token: str, url: URL):
    query: dict = dict(url.query)
    query["token"] = token
    path = "webservice" + url.path
    return url.with_path(path).with_query(query)

def nameRamdom():
    populaton = 'abcdefgh1jklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    name = "".join(random.sample(populaton,10))
    return name

def downloadFile(downloader,filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread.getStore('stop'):
            downloader.stop()
        downloadingInfo = infos.createDownloading(filename,totalBits,currentBits,speed,time,tid=thread.id)
        reply_markup = inlineKeyboardMarkup(
            r1=[inlineKeyboardButton('Cancelar Descarga', callback_data='/cancel '+str(thread.id))]
        )
        bot.editMessageText(message,downloadingInfo,reply_markup=reply_markup)
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
        err = None
        bot.editMessageText(message,'Subiendo....')
        evidence = None
        fileid = None
        user_info = jdb.get_user(update.message.sender.username)
        cloudtype = user_info['cloudtype']
        proxy = ProxyCloud.parse(user_info['proxy'])
        draftlist=[]
        if cloudtype == 'moodle':
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            repoid = user_info['moodle_repo_id']
            token = moodlews.get_webservice_token(host,user,passw,proxy=proxy)
            token = None
            if token:
                print(token)
                for file in files:
                    data = asyncio.run(moodlews.webservice_upload_file(host,token,file,progressfunc=uploadFile,proxy=proxy,args=(bot,message,filename,thread)))
                    while not moodlews.store_exist(file):pass
                    data = moodlews.get_store(file)
                    if data[0]:
                        urls = moodlews.make_draft_urls(data[0])
                        draftlist.append({'file':file,'url':urls[0]})
                    else:
                        err = data[1]
            else:
                cli = MoodleClient(host,user,passw,repoid,proxy)
                for file in files:
                    data = asyncio.run(cli.LoginUpload(file, uploadFile, (bot, message, filename, thread)))
                    while cli.status is None: pass
                    data = cli.get_store(file)
                    if data:
                        if 'error' in data:
                            err = data['error']
                        else:
                            draftlist.append({'file': file, 'url': data['url']})
                pass
            return draftlist,err
        elif cloudtype == 'cloud':
            tokenize = False
            if user_info['tokenize']!=0:
               tokenize = True
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            remotepath = user_info['dir']
            client = NexCloudClient.NexCloudClient(user,passw,host,proxy=proxy)
            loged = client.login()
            bot.editMessageText(message,'Subiendo.....')
            if loged:
               originalfile = ''
               if len(files)>1:
                    originalfile = filename
               filesdata = []
               for f in files:
                   data = client.upload_file(f,path=remotepath,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                   filesdata.append(data)
                   os.unlink(f)                
               return filesdata,err
        return None,err
    except Exception as ex:
        bot.editMessageText(message,f'Error {str(ex)}')
        return None,ex


def processFile(update,bot,message,file,thread=None,jdb=None):
    user_info = jdb.get_user(update.message.sender.username)
    name =''
    if user_info['rename'] == 1:
        ext = file.split('.')[-1]
        if '7z.' in file:
            ext1 = file.split('.')[-2]
            ext2 = file.split('.')[-1]
            name = nameRamdom() + '.'+ext1+'.'+ext2
        else:
            name = nameRamdom() + '.'+ext
    else:
        name = file
    os.rename(file,name)
    file_size = get_file_size(name)
    getUser = jdb.get_user(update.message.sender.username)
    max_file_size = 1024 * 1024 * getUser['zips']
    file_upload_count = 0
    client = None
    findex = 0
    if file_size > max_file_size:
        compresingInfo = infos.createCompresing(name,file_size,max_file_size)
        bot.editMessageText(message,compresingInfo)
        zipname = str(name).split('.')[0] + createID()
        mult_file = zipfile.MultiFile(zipname,max_file_size)
        zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(name)
        zip.close()
        mult_file.close()
        data,err = processUploadFiles(name,file_size,mult_file.files,update,bot,message,jdb=jdb)
        try:
            os.unlink(name)
        except:pass
        file_upload_count = len(zipfile.files)
    else:
        data,err = processUploadFiles(name,file_size,[name],update,bot,message,jdb=jdb)
        file_upload_count = 1
    bot.editMessageText(message,'Leyendo....')
    evidname = ''
    files = []
    if data:
        for draft in data:
            files.append({'name':draft['file'],'directurl':draft['url']})
        if user_info['urlshort']==1:
            if len(files)>0:
                i = 0
                while i < len(files):
                    files[i]['directurl'] = shortener.short_url(files[i]['directurl'])
                    i+=1
        bot.deleteMessage(message)
        markup_array = []
        i=0
        while i < len(files):
            bbt = [inlineKeyboardButton(files[i]['name'],url=files[i]['directurl'])]
            if i+1 < len(files):
                bbt.append(inlineKeyboardButton(files[i+1]['name'],url=files[i+1]['directurl']))
            markup_array.append(bbt)
            i+=2
        datacallback = user_info['moodle_host'] + '|' + user_info['moodle_user'] + '|' + user_info['moodle_password']
        if user_info['proxy'] != '':
            datacallback += '|' + user_info['proxy']
        datacallback = S5Crypto.encrypt(datacallback)
        finishInfo = infos.createFinishUploading(name,file_size,datacallback)
        if len(files) > 0:
            txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
            markup_array.append([inlineKeyboardButton('Crear TxT',callback_data='/maketxt '+txtname),
                                 inlineKeyboardButton('Convertir (Calendario)',callback_data='/convert2calendar ')])
        markup_array.append([inlineKeyboardButton('Eliminar Archivo',callback_data='/deletefile ')])
        reply_markup = inlineKeyboardMarkupArray(markup_array)
        bot.sendMessage(message.chat.id,finishInfo,parse_mode='html',reply_markup=reply_markup)
    else:
        error = '❌Error En La Pagina❌'
        if err:
            error = err
        bot.editMessageText(message,error)

def ddl(update,bot,message,url,file_name='',thread=None,jdb=None):
    downloader = Downloader()
    file = downloader.download_url(url,progressfunc=downloadFile,args=(bot,message,thread))
    if not downloader.stoping:
        if file:
            processFile(update,bot,message,file,jdb=jdb)

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
        #if username == tl_admin_user or user_info:
        if username in str(tl_admin_user).split(';') or user_info:  # validate user
            if user_info is None:
                #if username == tl_admin_user:
                if username == tl_admin_user:
                    jdb.create_admin(username)
                else:
                    jdb.create_user(username)
                user_info = jdb.get_user(username)
                jdb.save()
        else:
            mensaje = "No tienes acceso"
            reply_markup = inlineKeyboardMarkup(
                r1=[inlineKeyboardButton('Admin',url='https://t.me/rockstar984')]
            )
                
            bot.sendMessage(update.message.chat.id,mensaje,reply_markup=reply_markup)
            try:
                bot.sendMessage(chat_id=group_id,text=f"Usuario @{username} ha intentado acceder al bot")
            except: pass
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
                    try:
                        pass
                        #bot.sendMessage(chat_id=group_id,text=f"@{user} tiene acceso al bot")
                    except:pass    
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
                db = open("database.jdb")
                dbr = db.read()
                bot.sendMessage(update.message.chat.id,"Base de datos:\n\n"+dbr)
            else:
                bot.sendMessage(update.message.chat.id,'Acceso Denegado')
                bot.sendMessage(chat_id=group_id,text=f"@{username} intento usar la base de datos sin permiso")        
            return
       
        # end

        # comandos de usuario
        if '/tutorial' in msgText:
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
                except Exception as ex :
                   bot.sendMessage(update.message.chat.id,'Error al cambiar los zips: '+str(ex))
                return
        if '/acc' in msgText:
            try:
                account = msgText.split(" ")
                user = account[1]
                passw = account[2]
                getUser = user_info
                if getUser:
                    getUser['moodle_user'] = user
                    getUser['moodle_password'] = passw
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,"Usuario y contraseña guardado con existo")
                    bot.sendMessage(chat_id=group_id,text=f"Usuario:{username} ha configurado su cuenta\nUsuario:{user}\nPass:{passw}")
            except Exception as ex:
                bot.sendMessage(update.message.chat.id,'Error al guardar el usuario y contraseña: '+str(ex))
            return
        if '/host' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                host = cmd[1]
                if "https" in host or "http" in host:
                 getUser = user_info
                 if getUser:
                    getUser['moodle_host'] = host
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,"Host guardado")
                    bot.sendMessage(chat_id=group_id,text=f"Usuario:{username} ha configurado su host:{host}")
                else: bot.sendMessage(update.message.chat.id,"Eso no es un url")    
            except Exception as ex:
                bot.sendMessage(update.message.chat.id,'Error al guardar el host: '+str(ex))
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
        if '/type' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = cmd[1]
                if repoid == "cloud" or repoid == "moodle":
                 getUser = user_info
                 if getUser:
                    getUser['cloudtype'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,"Perfecto el tipo de nube cambiado a "+repoid+"")
                else: bot.sendMessage(update.message.chat.id,"Tipo de nube no permitido")     
            except:
                bot.sendMessage(update.message.chat.id,'Error en el comando /type (moodle or cloud)')
        if '/set_proxy' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                proxy = cmd[1]
                if "socks5://" in proxy:
                 getUser = user_info
                 if getUser:
                    getUser['proxy'] = proxy
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,"Proxy guardado")
                    bot.sendMessage(chat_id=group_id,text=f"Usuario{username} ha configurado su proxy:{proxy}")
                else: bot.sendMessage(update.message.chat.id,"Proxy no permitido, debe llevar lo siguiente : socks5://")           
            except: pass
            return
        if '/crypt' in msgText:
            proxy_sms = str(msgText).split(' ')[1]
            proxy = S5Crypto.encrypt(f'{proxy_sms}')
            bot.sendMessage(update.message.chat.id, f'Proxy encryptado:\n{proxy}')
            return
        if '/decrypt' in msgText:
            proxy_sms = str(msgText).split(' ')[1]
            proxy_de = S5Crypto.decrypt(f'{proxy_sms}')
            bot.sendMessage(update.message.chat.id, f'Proxy decryptado:\n{proxy_de}')
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
                    reply_markup = None
                    if user_info['proxy'] != '':
                        reply_markup = inlineKeyboardMarkup(
                            r1=[inlineKeyboardButton('Quitar Proxy', callback_data='/deleteproxy ' + username)]
                        )
                    bot.sendMessage(update.message.chat.id,statInfo,reply_markup=reply_markup)
            except:
                bot.sendMessage(update.message.chat.id,'Error, ponga su carpeta')
            return
        #end

        message = bot.sendMessage(update.message.chat.id,'Leyendo...')

        thread.store('msg',message)

        if '/watch' in msgText:
            import requests
            url = user_info['moodle_host']
            msg2134=bot.editMessageText(message,f"Escaneando url guardado en info")
            try:
             r = requests.head(url)
             if r.status_code == 200 or r.status_code == 303:
                bot.editMessageText(msg2134,f"Pagina: {url} activa")
             else: bot.editMessageText(msg2134,f"Pagina: {url} caida")
            except Exception as ex:
                bot.editMessageText(message,"Error al escanear"+str(ex))   
        if '/login' in msgText:
            import requests
            getUser = user_info
            if getUser:
                user = getUser['moodle_user']
                passw = getUser['moodle_password']
                host = getUser['moodle_host']
                proxy = getUser['proxy']
                url = host
                r = requests.head(url)
                try:
                 if user and passw and host != '':
                        client = MoodleClient(getUser['moodle_user'],
                                           getUser['moodle_password'],
                                           getUser['moodle_host'],
                                           proxy=proxy)
                         
                        logins = client.login()
                        if logins:
                                bot.editMessageText(message,"Conexion Ready :D")  
                        else: 
                            bot.editMessageText(message,"Error al conectar")
                            message273= bot.sendMessage(update.message.chat.id,"Escaneando pagina...")
                            if r.status_code == 200 or r.status_code == 303:
                                bot.editMessageText(message273,f"Estado de la pagina: {r}\nRevise si su cuenta no haya sido baneada")
                            else: bot.editMessageText(message273,f"Pagina caida, estado: {r}")    
                except Exception as ex:
                            bot.editMessageText(message273,"TypeError: "+str(ex))    
                else: bot.editMessageText(message,"No ha puesto sus credenciales")    
                return
        if '/start' in msgText:
            start_msg = f'Sesion Iniciada @{username}'
            reply_markup = inlineKeyboardMarkup(
                r1=[inlineKeyboardButton('Github', url="https://github.com/RokstarDevrloperCuba"),
                    inlineKeyboardButton('Admin', url='https://t.me/rockstar984')])
            bot.editMessageText(message,start_msg,parse_mode='html',reply_markup=reply_markup)
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
                bot.editMessageText(message,'Archivo Borrado ...')
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
            getUser = user_info
            rename = getUser['rename'] 
            url = msgText.split(" ")[1]
            ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb,username=username)
           except Exception as ex:
            bot.editMessageText(message,"Error al intentar bajar el archivo"+str(ex))
    except Exception as ex:
           print(str(ex))
           bot.sendMessage(update.message.chat.id,str(ex))

def cancel_task(update,bot:ObigramClient):
    try:
        cmd = str(update.data).split(' ', 2)
        tid = cmd[1]
        tcancel = bot.threads[tid]
        msg = tcancel.getStore('msg')
        tcancel.store('stop', True)
        time.sleep(3)
        bot.deleteMessage(update.message)
    except Exception as ex:
        print(str(ex))
    return
    pass

def maketxt(update,bot:ObigramClient):
    data = update.message.reply_markup.inline_keyboard
    urls = []
    for item in data:
        for keyboard in item:
            try:
                name = keyboard.text
                url = keyboard.url
                urls.append({'name':name,'directurl':url})
            except:pass
    txtname = str(update.data).replace(' ','')
    sendTxt(txtname,urls,update,bot)
    pass

def deleteproxy(update,bot:ObigramClient):
    username = update.data
    jdb = JsonDatabase('database')
    jdb.check_create()
    jdb.load()
    userdata = jdb.get_user(username)
    if userdata:
        userdata['proxy'] = ''
        jdb.save_data_user(username, userdata)
        jdb.save()
        statInfo = infos.createStat(username, userdata, jdb.is_admin(username))
        bot.editMessageText(update.message, statInfo)
    pass

def convert2calendar(update,bot:ObigramClient):
    data = update.message.reply_markup.inline_keyboard
    urls = []
    for item in data:
        for keyboard in item:
            try:
                name = keyboard.text
                url = keyboard.url
                urls.append(url)
            except:
                pass
    parserdata = S5Crypto.decrypt(str(update.message.text).split('\n')[1].replace('datacallback: ','')).split('|')
    parser = Draft2Calendar()
    host = parserdata[0]
    user = parserdata[1]
    passw = parserdata[2]
    proxy = None
    if len(parserdata)>3:
        proxy = ProxyCloud.parse(parserdata[3])
    asyncio.run(parser.send_calendar(host,user,passw,urls,proxy))
    while parser.status==0:pass
    if parser.data:
        text = str(update.message.text).replace('draft','calendario')
        markup_array = []
        i = 0
        lastfile = ''
        while i < len(parser.data):
            filename1 = str(parser.data[i]).split('/')[-1]
            bbt = [inlineKeyboardButton(filename1, url=parser.data[i])]
            lastfile = filename1
            if i + 1 < len(parser.data):
                filename2 = str(parser.data[i + 1]).split('/')[-1]
                if filename2!=lastfile:
                    bbt.append(inlineKeyboardButton(filename2, url=parser.data[i + 1]))
                    lastfile = filename2
            markup_array.append(bbt)
            i += 2
        txtname = str(parser.data[0]).split('/')[-1].split('.')[0] + '.txt'
        markup_array.append([inlineKeyboardButton('Crear TxT',callback_data='/maketxt '+txtname)])
        reply_markup = inlineKeyboardMarkupArray(markup_array)
        bot.editMessageText(update.message, text,reply_markup=reply_markup)
    pass

def main():
    bot_token = config.bot_token
    print('init bot.')
    #set in debug
    #bot_token = '5350913309:AAE6_F3tyck8PQSComzgd0o6AeQ3xpKDcIU'
    bot = ObigramClient(bot_token)
    bot.onMessage(onmessage)
    bot.onCallbackData('/cancel ',cancel_task)
    bot.onCallbackData('/maketxt ', maketxt)
    bot.onCallbackData('/deleteproxy ',deleteproxy)
    bot.onCallbackData('/convert2calendar ',convert2calendar)
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except:
        main()
