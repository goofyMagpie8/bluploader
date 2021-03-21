#! /usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from argparse import ArgumentParser
from pathlib import Path
import json
import os
import subprocess
import tempfile
from guessit import guessit
from imdb import IMDb
import pickle
import math
import configparser
config = configparser.ConfigParser(allow_no_value=True)
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
import re
from pymediainfo import MediaInfo
from threading import Thread









def createconfig(args):
    try:
        configpath=args.config

        config.read(configpath)

    except:
        print("something went wrong")
        return args


    if args.imgbb==None:
        args.imgbb=config['api']['imgbb']
    if args.bluapi==None:
        args.bluapi=config['api']['bluapi']
    if args.tmdb==None:
        args.tmdb=config['api']['tmdb']
    if args.torrentdir==None:
        args.torrentdir=config['general']['torrentdir']
    if args.autotype==None:
        args.autotype=config['general']['autotype']
    if args.stream==None:
        args.stream=config['general']['stream']
    if args.anon==None:
        args.anon=config['general']['anon']
    if args.userid==None:
        args.userid=config['general']['userid']
    if args.txtoutput==None:
        args.txtoutput=config['general']['txtoutput']
    if args.autoupload==None:
        args.autoupload=config['general']['autoupload']
    if args.media==None:
        args.media=config['general']['media']
    if args.font==None:
        args.font=config['general']['font']
    if args.announce==None:
        args.announce=config['general']['announce']
    if args.mtn=="mtn" and len(config['programs']['mtn'])!=0:
        args.mtn=config['programs']['mtn']
    if args.dottorrent==None and len(config['programs']['dottorrent'])>0 :
        args.dottorrent=config['programs']['dottorrent']
    if args.oxipng=="oxipng" and len(config['programs']['oxipng'])!=0:
        args.oxipng=config['programs']['oxipng']
    if args.compress==None and config['general']['compress']=="yes":
        args.compress=config['general']['compress']
    return args


def create_binaries(args):
    print("Setting up Binaries")
    workingdir=os.path.dirname(os.path.abspath(__file__))
    if args.dottorrent==None:
        if which("dottorrent")!=None and len(which('dottorrent'))>0:
            args.dottorrent=which('dottorrent')
        else:
            dottorrent=os.path.join(workingdir,"bin","dottorrent")
            args.dottorrent=dottorrent
    if args.oxipng==None and sys.platform=="linux":
        if which("oxipng")!=None and len(which('oxipng'))>0:
            args.oxipng=which('oxipng')
        else:
            oxipng=os.path.join(workingdir,"bin","oxipng")
            args.oxipng=oxipng

    if args.oxipng==None and sys.platform=="win32":
       if which("oxipng.exe")!=None and len(which('oxipng.exe'))>0:
            args.oxipng=which('oxipng.exe')
       else:
           oxipng=os.path.join(workingdir,"bin","oxipng.exe")
           args.oxipng=oxipng

    if args.mtn==None and sys.platform=="linux":
        if which("mtn")!=None and len(which('mtn'))>0:
            args.mtn=which('mtn')
        else:
            mtn=os.path.join(workingdir,"bin","mtn")
            args.mtn=mtn
    if args.mtn==None and sys.platform=="win32":
        if which("mtn")!=None and len(which('mtn.exe'))>0:
            args.mtn=which('mtn.exe')
        else:
            mtn=os.path.join(workingdir,"bin","mtn-win32","bin","mtn.exe")
            args.mtn=mtn


def create_upload_form(arguments,entyname=None):
    if entyname==None:
        uploadpath=args.media
    else:
        uploadpath=args.media+entyname


    #iF The Upload path is a diresctory pick a video file for screenshots,mediainfo,etc
    if os.path.isdir(uploadpath):
          for enty in os.scandir(uploadpath):
              if re.search(".mkv",enty.name)!=None or re.search(".mp4",enty.name)!=None:
                  path=uploadpath+"/"+enty.name
    #Else just use the file itself
    else:
        path=uploadpath


    typeid=setTypeID(path,args)
    setType(path,args)
    title=getTitle(uploadpath,args,typeid)
    print(title)
    correct=input("Title is it Correct for Blu?:")


    if correct!="y" and correct!="yes" and correct!="Yes" and correct!="YES" and correct!="Y":
         title_completer = WordCompleter([title])
         title = prompt('Enter Title: ', completer=title_completer,complete_while_typing=True)

    dir = tempfile.TemporaryDirectory()
    imgs = Thread(target = create_images, args = (path,args,dir))
    imgs.start()
    torrentpath= args.torrentdir +"[Blutopia]" + title + '.torrent'
    # torrentpath=f'"{torrentpath}"'
    torrent = Thread(target = create_torrent, args = (uploadpath,args,torrentpath))
    torrent.start()

    cat=setCat(args.format)
    res=setResolution(path)
    if check_dupe(typeid,title,args,cat,res)==False:
        return


    imdbid = getimdb(path)
    tmdbid=IMDBtoTMDB(imdbid.movieID,args)
    torrent.join()
    imgs.join()




    form = {'imdb' : imdbid.movieID,
            'name' : title,
            'description' : upload_image(dir,args),
            'category_id' : cat,
            'tmdb': tmdbid,
            'type_id': typeid,
            'resolution_id' : res,
            'user_id' : args.userid,
            'anonymous' : args.anon,
            'stream'    : args.stream,
            'sd'        : is_sd(path),
            'tvdb'      : '0',
            'igdb'  : '0' ,
            'mal' : '0',
            'mediainfo' : get_mediainfo(path)
            }



    output=os.path.join(tempfile.gettempdir(), os.urandom(24).hex()+".txt")
    if args.txtoutput=="yes":
        txt=open(output, 'a+')
        for key, value in form.items():
            txt.write('%s:\n\n%s\n\n' % (key, value))
        txt.close()

        output = {'file': open(output,'r')}
        post=requests.post(url="https://uguu.se/api.php?d=upload-tool",files=output)
        print(post.text)

    if args.autoupload=="yes":
        torrent = {'torrent': open(torrentpath,'rb')}
        torrenturl="https://blutopia.xyz/api/torrents/upload?api_token=" + args.bluapi
        upload=requests.post(url=torrenturl,files=torrent, data=form)
        print(upload.text)



def create_torrent(path,args,torrentpath):
   print("Creating Torrent")
   t=subprocess.run([args.dottorrent,'-p','--source', 'BLU','-t',args.announce,path,torrentpath],stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)



def IMDBtoTMDB(imdbid,args):
  format=args.format
  url="https://api.themoviedb.org/3/find/tt" + str(imdbid) +"?api_key="  +args.tmdb+"&language=en-US&external_source=imdb_id"
  list=requests.get(url)
  if(format=="TV"):
       format='tv_results'
  if(format=="Movie"):
       format='movie_results'
  print(url)


  id=list.json()[format]
  if len(id)==0:
      imdbid= input("auto imdb is probably wrong, please manually enter imdb excluding the tt: ")
      url="https://api.themoviedb.org/3/find/tt" + str(imdbid) +"?api_key="  +args.tmdb+"&language=en-US&external_source=imdb_id"
      list=requests.get(url)
      if(format=="TV"):
            format='tv_results'
      if(format=="Movie"):
            format='movie_results'
      print(url)
      id=list.json()[format]


  id=id[0]
  id=id['id']
  return id




def getimdb(path):
   details=guessit(path)
   title = details['title']
   if 'year' in details:
        title = "{} {}".format(title, details['year'])
   results = IMDb().search_movie(title)
   if len(results)==0 :
        print("Unable to find imdb")
        id = input("Enter Title or imdb(no tt) ")
        if re.search("tt",id)!=None:
            results=IMDb().get_movie(id)
        else:
            results = IMDb().search_movie(id)



   if isinstance(results, list)!=True:
       return results

   counter=0
   accept=False
   print("Searching for movie/TV Show on IMDB","\n")
   while accept!="True"and accept!="Y" and accept!="Yes" and accept!="YES" and accept!="y":
       if counter==6 or counter>len(results):
           print("correct title not found")
           id = input("Enter imdb(no tt) ")
           results=IMDb().get_movie(id)
           return results
       title=results[counter]['title']
       year=str(results[counter]['year'])
       t=f"{title}  {{ Movie Released-{year}}}"
       print(t)
       accept=input(" is this Search result correct?:")
       if len(accept)==0 or accept=="N" or accept=="No" or accept=="n" or accept=="NO":
            counter=counter+1
   return results[counter]


















def getTitle(path,args,source):
    input_title=os.path.basename(path)
    output_title=""
    info=guessit(input_title)
    name=info.get("title")
    year=info.get("year","")
    res=  info.get("screen_size","")
    group=info.get("release_group","Unknown")
    channels=info.get("audio_channels","")
    codec=info.get("video_codec")
    audio=getAudio(info.get("audio_codec",""),info.get("audio_channels",""), info.get("audio_profile",""))
    extra=get_extra(input_title,info)
    season="S0"+info.get("season","")
    if args.format=="Movie" and (re.search("[bB][lL][uU][rR]",input_title)!=None or re.search("[bB][lL][uU]-[rR]",input_title)!=None ):
        output_title=f"{name} {year} {res} Blu-ray AVC REMUX {extra} "
    elif args.format=="Movie" and re.search("[bB][lL][uU]",input_title)!=None:
        output_title=f"{name} {year} {res} Blu-ray AVC {extra} "
    elif args.format=="Movie" and (re.search("[dD][vV][dD][rR]",input_title)!=None or re.search("[dD][vV][dD]-[rR]",input_title)!=None ):
        output_title=f"{name} {year} {res} DVD REMUX {extra} "
    elif args.format=="Movie" and re.search("[dD][vV][dD]",input_title)!=None:
        output_title=f"{name} {year} {res} DVD {extra} "
    elif args.format=="Movie" and (re.search("[wW][eE][bB][dD]",input_title)!=None or re.search("[wW][eE][bB]-[dD]",input_title)!=None ):
        output_title=f"{name} {year} {res} WEB-DL {extra} "
    elif args.format=="Movie" and (re.search("[wW][eE][bB][rR]",input_title)!=None or re.search("[wW][eE][bB]-[rR]",input_title)!=None ):
        output_title=f"{name} {year} {res} WEB-RIP {extra} "

    if args.format=="TV" and (re.search("[bB][lL][uU][rR]",input_title)!=None or re.search("[bB][lL][uU]-[rR]",input_title)!=None ):
        output_title=f"{name} {year} {season} {res} Blu-ray AVC REMUX  {extra} "
    elif args.format=="TV" and re.search("[bB][lL][uU]",input_title)!=None:
        output_title=f"{name} {year} {season} {res} Blu-ray AVC {extra} "
    elif args.format=="TV" and (re.search("[dD][vV][dD][rR]",input_title)!=None or re.search("[dD][vV][dD]-[rR]",input_title)!=None ):
        output_title=f"{name} {year} {season} {res} DVD REMUX {extra} "
    elif args.format=="TV" and re.search("[dD][vV][dD]",input_title)!=None:
        output_title=f"{name} {year} {season} {res} DVD {extra} "
    elif args.format=="TV" and (re.search("[wW][eE][bB][dD]",input_title)!=None or re.search("[wW][eE][bB]-[dD]",input_title)!=None ):
        output_title=f"{name} {year} {season} {res} WEB-DL {extra} "
    elif args.format=="TV" and (re.search("[wW][eE][bB][rR]",input_title)!=None or re.search("[wW][eE][bB]-[rR]",input_title)!=None ):
        output_title=f"{name} {year} {season} {res} WEB-RIP {extra} "

    output_title=re.sub("\."," ",output_title)
    output_title=re.sub("  "," ",output_title)
    tag=getTag(source,audio,group,codec)
    output_title=f"{output_title}{tag}"
    return output_title



    return output_title
def getTag(source,audio,group,codec):
    if source=="12" or source=="6":
        codec='x'+codec[2:]
        tag=f"{audio} {codec}-{group}"
    elif source=="4" or source=="5":
        tag=f"{audio} {codec}-{group}"
    else:
        tag=f"{audio}-{group}"
    tag=re.sub("  "," ",tag)
    tag=re.sub("^\s","",tag)
    return tag


def getAudio(audio,channels,profile):
    output=""

    if isinstance(audio,list):
        for element in audio:
            output=output+" "+element
    elif audio=="":
        pass
    else:
        output=output+audio
    if profile=="Master Audio":
        output=output+" MA"
    if channels!="":
        output=output+" "+channels
    return output

def get_extra(title,info):
    extra=""
    if re.search("atmos",title,re.IGNORECASE)!=None:
        extra=extra+"ATMOS"
    return extra

def setTypeID(path,args):
    if args.autotype=="yes":
        details=guessit(path)
        source = details['source']


        if (source=="Blu-ray" or source=="HD-DVD" or source=="Ultra HD Blu-ray") and re.search("[rR][eE][mM][uU][xX]",path)==None and re.search("[xX]26[45]",path)==None:
            source = '1'
        elif (source=="Blu-ray" or source=="HD-DVD" or source=="Ultra HD Blu-ray") and re.search("[rR][eE][mM][uU][xX]",path)!=None:
            source = '3'
        elif (source=="Blu-ray" or source=="HD-DVD" or source=="Ultra HD Blu-ray") and re.search("[xX]26[45]",path)!=None:
            source = '12'
        elif source=="Web" and (re.search("[wW][eE][bB]-[dD][lL]",path)!=None or re.search("[wW][eE][bB][dD][lL]",path)!=None or re.search("[wW][eE][bB]",path)!=None) and (re.search("[wW][eE][bB]-[rR][iI][pP]",path)==None and re.search("[wW][eE][bB][rR][iI][pP]",path)==None) :
            source = '4'
        elif source=="Web" and (re.search("[wW][eE][bB]-[rR][iI][pP]",path)!=None or re.search("[wW][eE][bB][rR][iI][pP]",path)!=None):
            source = '5'
        elif source=="Analog HDTV" or source=="HDTV" or source=="Ultra HDTV" or source=="TV":
            source = '6'
    else:
        print(path,"\n")
        print("FULL_DISC = '1' REMUX = '3' ENCODE = '12' WEBDL = '4' WEBRIP= '5' HDTV= '6'","\n")
        source = input("Enter your Number ")
    return source


def setResolution(path):
   details=guessit(path)
   resolution = details['screen_size']
   if resolution=="2160p":
        resolution="1"
   elif resolution=="1080p":
        resolution="2"
   elif resolution=="1080i":
       resolution="3"
   elif resolution=="720p":
       resolution="5"
   elif resolution=="576p":
       resolution="6"
   elif resolution=="576i":
       resolution="7"
   elif resolution=="480p":
       resolution="8"
   elif resolution=="480i":
       resolution="9"
   elif resolution=="8640p":
       resolution="10"
   elif resolution=="4320p":
      resolution="11"
   else:
      resolution="10"
   return resolution

def is_sd(path):
    details=guessit(path)
    resolution = details['screen_size']
    if resolution=="2160p" or resolution=="1080p" or resolution=="1080i" or resolution=="720p" or resolution=="8640p" or resolution=="4320p":
      resolution="0"
    else:
      resolution="1"
    return resolution



def setType(path,args):
    if args.autotype=="yes":
        details=guessit(path)
        format = details['type']
        if(format=="episode"):
            format = 'TV'
        else:
            format = 'Movie'
    else:
        print(path,"\n")
        print("What type of file are you uploading","\n")
        format = input("Enter TV or Movie: ")
    args.format=format

def check_dupe(typeid,title,args,cat,res):
    details=guessit(title)
    title = details['title']
    if details.get("season")!=None:
        title=title+" S0"+str(details["season"])

    if 'year' in details:
        title = "{} {}".format(title, details['year'])
    url="https://blutopia.xyz/api/torrents/filter?name="+title+"&categories[]="+cat+"&types[]="+typeid+"&resolution[]="+res+"&api_token=" + args.bluapi
    dupes=requests.get(url=url)
    dupes=dupes.json()
    print(url,"\n")

    number=len(dupes["data"])
    if number==0:
        return True
    for entry in range(0,number):
        print("name:",dupes["data"][entry]["attributes"]["name"])
    upload=input("Possible Dupes Found Do you Still want to Upload?: ")
    if upload=="y" or upload=="Y" or upload=="yes" or upload=="YES" or upload=="Yes":
        return True
    else:
        return False


def get_mediainfo(path):
    media_info = MediaInfo.parse(path,output="STRING",full=False)
    media_info=media_info.encode(encoding='utf8')
    media_info=media_info.decode('utf8', 'strict')
    return media_info
def create_images(path,args,dir):
    #uploading
    print("Creating Images")
    mtn=args.mtn
    oxipng=args.oxipng


    media_info = MediaInfo.parse(path)
    for track in media_info.tracks:
        if track.track_type == 'Video':
            interval=math.ceil(float(track.duration)/10000)
    t=subprocess.run(['mtn','-f',args.font,'-o','.png','-w','0','-P','-s',str(interval),'-I',path,'-O',dir.name],stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    #delete largest pic


    max=0
    delete=""
    for filename in os.listdir(dir.name):
       filename=dir.name +'/'+filename
       temp=os.path.getsize(filename)
       if(temp>max):
            max=temp
            delete=filename
    os.remove(delete)
    home= os.getcwd()
    os.chdir(dir.name)




    if args.compress=="=yes":
        for filename in os.listdir(dir.name):
            subprocess.run(['oxipng','-o','6','strip safe',filename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)




def upload_image(dir,args):
    home= os.getcwd()
    url='https://api.imgbb.com/1/upload?key=' + args.imgbb
    text=os.path.join(tempfile.gettempdir(), os.urandom(24).hex())
    textinput= open(text,"w+")
    for filename in os.listdir(dir.name):
         image=dir.name+'/'+filename
         image = {'image': open(image,'rb')}
         upload=requests.post(url=url,files=image)
         upload=upload.json()['data']['url_viewer']
         upload=requests.post(url=upload)
         link = BeautifulSoup(upload.text, 'html.parser')
         link = link.find('input',{'id' :'embed-code-5'})
         link=link.attrs['value']+" "
         textinput.write(link)
    textinput.close()
    textoutput= open(text,"r")
    os.chdir(home)
    return textoutput.read()


def setCat(format):
    if format=="Movie":
        return "1"
    if format=="TV":
        return "2"



if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--media",default=None)
    parser.add_argument("--imgbb",default=None)
    parser.add_argument("--config",default=None)
    parser.add_argument("--tmdb",default=None)
    parser.add_argument("--bluapi",default=None)
    parser.add_argument("--torrentdir",default=None)
    parser.add_argument("--autotype",default=None)
    parser.add_argument("--stream",default=None)
    parser.add_argument("--userid",default=None)
    parser.add_argument("--anon",default=None)
    parser.add_argument("--txtoutput",default=None)
    parser.add_argument("--autoupload",default=None)
    parser.add_argument("--font",default=None)
    parser.add_argument("--compress",default=None)
    parser.add_argument("--announce",default=None)
    parser.add_argument("--format",default=None)
    parser.add_argument("--mtn",default="mtn")
    parser.add_argument("--oxipng",default="oxipng")
    parser.add_argument("--dottorrent",default="dottorrent")
    parser.add_argument("--images",action='store_true')

    args = parser.parse_args()
    createconfig(args)
    create_binaries(args)
    print(args)
    if os.path.isdir(args.media)==False:
        if args.images:
            dir = tempfile.TemporaryDirectory()
            create_images(args.media,args,dir)
            imgs=upload_image(dir,args)
            print(imgs)
            quit()
        create_upload_form(args)
        quit()
    keepgoing = "Yes"
    choices=os.listdir(args.media)
    if os.name != 'nt':
        from simple_term_menu import TerminalMenu
        menu = TerminalMenu(choices)
        while keepgoing=="Yes" or keepgoing=="yes" or keepgoing=="Y" or keepgoing=="y"  or keepgoing=="YES":
            menu_entry_index = menu.show()
            path=choices[menu_entry_index]
            print("\n")
            if args.images:
                dir = tempfile.TemporaryDirectory()
                vid=os.path.join(args.media,path)
                create_images(vid,args,dir)
                imgs=upload_image(dir,args)
                print(imgs)
                continue
            create_upload_form(args,path)
            keepgoing=input("Upload Another File: ")
        quit()
    while keepgoing=="Yes" or keepgoing=="yes" or keepgoing=="Y" or keepgoing=="y"  or keepgoing=="YES":
        for (i, item) in enumerate(choices):
            index="INDEX:"+str(i)
            print('[',index,item,']',end="  ")
            if (i-1)%2==0:
                print("\n")
        print("\n","\n")
        myindex=input("Enter the INDEX of the upload: ")
        path=choices[int(myindex)]
        print("\n")
        if args.images:
            dir = tempfile.TemporaryDirectory()
            vid=os.path.join(args.media,path)

            create_images(vid.media,args,dir)
            imgs=upload_image(dir,args)
            print(imgs)
            continue
        create_upload_form(args,path)
        keepgoing=input("Upload Another File: ")
