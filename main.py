from cProfile import run
import pstats
from pyobigram.utils import sizeof_fmt,get_file_size,createID,nice_time
from pyobigram.client import ObigramClient,inlineQueryResultArticle
from MoodleClient import MoodleClient

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
from draft_to_calendar import send_calendar
import config

usuaios_registers = []

group_id = config.groupid

def sign_url(token: str, url: URL):
    query: dict = dict(url.query)
    query["token"] = token
    path = "webservice" + url.path
    return url.with_path(path).with_query(query)

def nameRamdom(name):
    name = name
    return name    

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
                          elif user_info['uploadtype'] == 'draft':
                             fileid,resp = client.upload_file_draft(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          elif user_info['uploadtype'] == 'perfil':
                             fileid,resp = client.upload_file_perfil(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          elif user_info['uploadtype'] == 'blog':
                             fileid,resp = client.upload_file_blog(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                             draftlist.append(resp)
                          elif user_info['uploadtype'] == 'calendar':
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
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            remotepath = user_info['dir']
            client = NexCloudClient.NexCloudClient(user,passw,host,proxy=proxy)
            loged = client.login()
            bot.editMessageText(message,'Subiendo...')
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
        bot.editMessageText(message,f'❌Error {str(ex)}❌')


def processFile(update,bot,message,file,thread=None,jdb=None):
    user_info = jdb.get_user(update.message.sender.username)
    name =''
    if user_info['rename'] == 1:
        ext = file.split('.')[-1]
        if '7z.' in file:
            ext1 = file.split('.')[-2]
            ext2 = file.split('.')[-1]
            name = nameRamdom(name) + '.'+ext1+'.'+ext2
        else:
            name = nameRamdom(name) + '.'+ext
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
        client = processUploadFiles(name,file_size,mult_file.files,update,bot,message,jdb=jdb)
        try:
            os.unlink(name)
        except:pass
        file_upload_count = len(zipfile.files)
    else:
        client = processUploadFiles(name,file_size,[name],update,bot,message,jdb=jdb)
        file_upload_count = 1
        bot.editMessageText(message,'Terminando..')
    bot.editMessageText(message,"Error")   
    evidname = ''
    files = []
    if client:
        if getUser['cloudtype'] == 'moodle':
            if getUser['uploadtype'] == 'evidence':
                try:
                    evidname = str(name).split('.')[0]
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
            if getUser['uploadtype'] == 'draft' \
                    or getUser['uploadtype'] == 'perfil' \
                    or getUser['uploadtype'] == 'blog' \
                    or getUser['uploadtype'] == 'calendar'\
                    or getUser['uploadtype'] == 'calendarevea':
               for draft in client:
                   files.append({'name':draft['file'],'directurl':draft['url']})
        else:
            for data in client:
                files.append({'name':data['name'],'directurl':data['url']})
        if user_info['urlshort']==1:
            if len(files)>0:
                i = 0
                while i < len(files):
                    files[i]['directurl'] = shortener.short_url(files[i]['directurl'])
                    i+=1
        bot.deleteMessage(message.chat.id,message.message_id)
        finishInfo = infos.createFinishUploading(name,file_size,max_file_size,file_upload_count,file_upload_count,findex)
        filesInfo = infos.createFileMsg(name,files)
        bot.sendMessage(message.chat.id,finishInfo+'\n'+filesInfo,parse_mode='html')
        if len(files)>0:
            txtname = str(name).split('/')[-1].split('.')[0] + '.txt'
            sendTxt(txtname,files,update,bot)
    else:
        bot.editMessageText(message,'Error')

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

        #set in debug
        tl_admin_user = config.admin

        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()

        user_info = jdb.get_user(username)
        #if username == tl_admin_user or user_info:
        if username in str(tl_admin_user).split(';') or user_info :  # validate user
            if user_info is None:
                #if username == tl_admin_user:
                if username == tl_admin_user:
                    jdb.create_admin(username)
                else:
                    jdb.create_user(username)
                user_info = jdb.get_user(username)
                jdb.save()
        else:
            msg323= "No tienes acceso"
            bot.sendMessage(update.message.chat.id,msg323)
            try:
                bot.sendMessage(chat_id=group_id,text=f"Usuario: @{username} ha intentado acceder al bot")
            except:pass     
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
                        bot.sendMessage(chat_id=group_id,text=f"@{user} tiene acceso al bot")
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
        if '/setevea' in msgText:
            getUser = user_info
            user = ''
            passw = ''
            hostmo = 'https://evea.uh.cu/'
            zips = 240
            repoid = 4
            uptype = 'calendarevea' 
            if getUser:
                getUser['moodle_user'] = user
                getUser['moodle_password'] = passw
                getUser['moodle_host'] = hostmo
                getUser['zips'] = zips
                getUser['uploadtype'] = uptype
                getUser['moodle_repo_id'] = repoid
                jdb.save_data_user(username,getUser)
                jdb.save()
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,f"Todo configurado para el host{hostmo}")
            return
        if '/seteva' in msgText:
            getUser = user_info
            user = ''
            passw = ''
            hostmo = 'https://eva.uo.edu.cu/'
            zips = 99
            repoid = 4
            uptype = 'calendar' 
            if getUser:
                getUser['moodle_user'] = user
                getUser['moodle_password'] = passw
                getUser['moodle_host'] = hostmo
                getUser['zips'] = zips
                getUser['uploadtype'] = uptype
                getUser['moodle_repo_id'] = repoid
                jdb.save_data_user(username,getUser)
                jdb.save()
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,f"Todo configurado para el host{hostmo}")
            return
        if '/setcursos' in msgText:
            getUser = user_info
            user = ''
            passw = ''
            hostmo = 'https://cursos.uo.edu.cu/'
            zips = 99
            repoid = 4
            uptype = 'draft' 
            if getUser:
                getUser['moodle_user'] = user
                getUser['moodle_password'] = passw
                getUser['moodle_host'] = hostmo
                getUser['zips'] = zips
                getUser['uploadtype'] = uptype
                getUser['moodle_repo_id'] = repoid
                jdb.save_data_user(username,getUser)
                jdb.save()
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,f"Todo configurado para el host{hostmo}")
            return
        if '/setedu' in msgText:
            getUser = user_info
            user = ''
            passw = ''
            hostmo = 'https://eduvirtual.uho.edu.cu/'
            zips = 2000
            repoid = 3
            uptype = 'blog' 
            if getUser:
                getUser['moodle_user'] = user
                getUser['moodle_password'] = passw
                getUser['moodle_host'] = hostmo
                getUser['zips'] = zips
                getUser['uploadtype'] = uptype
                getUser['moodle_repo_id'] = repoid
                jdb.save_data_user(username,getUser)
                jdb.save()
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,f"Todo configurado para el host{hostmo}")
            return
        if '/setuclv' in msgText:
            getUser = user_info
            user = ''
            passw = ''
            hostmo = 'https://moodle.uclv.edu.cu/'
            zips = 359
            repoid = 4
            uptype = 'calendar' 
            if getUser:
                getUser['moodle_user'] = user
                getUser['moodle_password'] = passw
                getUser['moodle_host'] = hostmo
                getUser['zips'] = zips
                getUser['uploadtype'] = uptype
                getUser['moodle_repo_id'] = repoid
                jdb.save_data_user(username,getUser)
                jdb.save()
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,f"Todo configurado para el host{hostmo}")
            return
        if '/shorturl' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    for user in jdb.items:
                        if jdb.items[user]['urlshort']==0:
                            jdb.items[user]['urlshort'] = 1
                            continue
                        if jdb.items[user]['urlshort']==1:
                            jdb.items[user]['urlshort'] = 0
                            continue
                    jdb.save()
                    bot.sendMessage(update.message.chat.id,"Acortador de enlaces activado")
                    statInfo = infos.createStat(username, user_info, jdb.is_admin(username))
                except Exception as ex:
                    bot.sendMessage(update.message.chat.id,"Error al activar el acortador de enlaces" + str(ex))
            return
        # end

        # comandos de usuario
        if '/tutorial' in msgText:
            tuto = open('tuto.txt','r')
            bot.sendMessage(update.message.chat.id,tuto.read())
            tuto.close()
            return
        if '/setproxy' in msgText:
            getUser = user_info
            if getUser:
                try:
                   pos = int(str(msgText).split(' ')[1])
                   proxy = str(listproxy[pos])
                   getUser['proxy'] = proxy
                   jdb.save_data_user(username,getUser)
                   jdb.save()
                   msg = 'Su Proxy esta Listo'
                   bot.sendMessage(update.message.chat.id,msg)
                except:
                   bot.sendMessage(update.message.chat.id,'❌Error en el comando /setproxy pos❌')
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
            return
        if '/setname' in msgText:
            #Selecciona el nombre que quieras
            name = msgText.split(" ")[1]
            nameRamdom(name)
            bot.sendMessage(update.message.chat.id,f"Nombre de los archivos cambiado a: {name}")
            return 
        if '/rename_on' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['rename'] = 1
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,"Rename on")
            except: bot.sendMessage(update.message.chat.id,"No se pudo activar el autonombrado")        
            return
        if '/rename_off' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['rename'] = 0
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,"Rename off")
            except: bot.sendMessage(update.message.chat.id,"No se pudo descativar el autonombrado")
            return
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
        if '/uptype' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                type = cmd[1]
                
                if "calendar" == type or "evidence" == type or "perfil" == type or "draft" == type or "blog" == type:   
                 getUser = user_info
                 if getUser:
                    getUser['uploadtype'] = type
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,f"Lugar de subida cambiado a: {type}")
                else: bot.sendMessage(update.message.chat.id,f"Uptype no permitido")      
            except Exception as ex:
                bot.sendMessage(update.message.chat.id,'Error en el comando uptype: '+str(ex))
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
             getUser = user_info
             if getUser:
                user = getUser['moodle_user']
                passw = getUser['moodle_password']
                host = getUser['moodle_host']
                proxy = getUser['proxy']
                if user and passw and host != '':
                        client = MoodleClient(getUser['moodle_user'],
                                           getUser['moodle_password'],
                                           getUser['moodle_host'],
                                           proxy=proxy)
                        logins = client.login()
                        if logins:
                                bot.editMessageText(message,"Conexion Ready :D")  
                        else: bot.editMessageText(message,"Error al conectar")                         
                else: bot.editMessageText(message,"No ha puesto sus credenciales")    
                return
        if '/start' in msgText:
           usuaios213 = []
           if username in usuaios213:
            start_msg2 = f"Ya iniciaste sesion @{username}"
            bot.editMessageText(message,start_msg2,parse_mode="html")
           else: 
            start_msg = f'Sesion Iniciada @{username}'
            bot.editMessageText(message,start_msg,parse_mode="html") 
            usuaios213.append(username)
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
           except Exception as ex:
            bot.editMessageText(message,"Error al intentar bajar el archivo"+str(ex)) 
    except Exception as ex:
           print(str(ex))


def main():
    bot_token = os.environ.get('bot_token')
    #set in debug
    bot_token = config.bot_token

    bot = ObigramClient(bot_token)
    bot.onMessage(onmessage)
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except:
        main()