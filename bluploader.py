#! /usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import subprocess
from argparse import ArgumentParser
from pathlib import Path
import json
import os
import tempfile
from guessit import guessit
from imdb import IMDb
import pickle
import subprocess
import math
import configparser
config = configparser.ConfigParser(allow_no_value=True)
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
import re








def createconfig(arguments):
    try:
        configpath=arguments.config

        config.read(configpath)

    except:
        print("something went wrong")
        return arguments


    if arguments.imgbb==None:
        arguments.imgbb=config['api']['imgbb']
    if arguments.bluapi==None:
        arguments.bluapi=config['api']['bluapi']
    if arguments.tmdb==None:
        arguments.tmdb=config['api']['tmdb']
    if arguments.torrentdir==None:
        arguments.torrentdir=config['general']['torrentdir']
    if arguments.autotype==None:
        arguments.autotype=config['general']['autotype']
    if arguments.stream==None:
        arguments.stream=config['general']['stream']
    if arguments.anon==None:
        arguments.anon=config['general']['anon']
    if arguments.userid==None:
        arguments.userid=config['general']['userid']
    if arguments.txtoutput==None:
        arguments.txtoutput=config['general']['txtoutput']
    if arguments.autoupload==None:
        arguments.autoupload=config['general']['autoupload']
    if arguments.media==None:
        arguments.media=config['general']['media']
    if arguments.font==None:
        arguments.font=config['general']['font']
    if arguments.announce==None:
        arguments.announce=config['general']['announce']
    if arguments.mtn=="mtn" and len(config['general']['mtn'])!=0:
        arguments.mtn=config['general']['mtn']
    if arguments.oxipng=="oxipng" and len(config['general']['oxipng'])!=0:
        arguments.oxipng=config['general']['oxipng']
    if arguments.mediainfo=="mediainfo" and len(config['general']['mediainfo'])!=0:
        arguments.mediainfo=config['general']['mediainfo']
    if arguments.compress==None and config['general']['compress']=="yes":
        arguments.compress=config['general']['compress']

    return arguments




def create_upload_form(arguments,entyname=None):
    if entyname==None:
        uploadpath=arguments.media
    else:
        uploadpath=arguments.media+entyname

    title=getTitle(uploadpath)

    #iF The Upload path is a directory pick a video file for screenshots,mediainfo,etc
    if Path(uploadpath).is_dir():
          for enty in os.scandir(uploadpath):
              if re.search(".mkv",enty.name)!=None or re.search(".mp4",enty.name)!=None:
                  path=uploadpath+"/"+enty.name
    #Else just use the file itself              
    else:
        path=uploadpath            

    typeid=setTypeID(path,arguments)
    format = setType(path,arguments)
    cat=setCat(format)
    res=setResolution(path)
    if check_dupe(typeid,title,arguments,cat,res)==False:
        return


    imdbid = getimdb(path)
    tmdbid=IMDBtoTMDB(imdbid.movieID,format,arguments)

    mediapath=os.path.join(tempfile.gettempdir(), os.urandom(24).hex())
    mediaInfo=get_mediainfo(path,mediapath,arguments)
    mediainfo=open(mediapath, 'r').read()

    form = {'imdb' : imdbid.movieID,
            'name' : title,
            'description' : createimages(path,arguments),
            'category_id' : cat,
            'tmdb': tmdbid,
            'type_id': typeid,
            'resolution_id' : res,
            'user_id' : arguments.userid,
            'anonymous' : arguments.anon,
            'stream'    : arguments.stream,
            'sd'        : is_sd(path),
            'tvdb'      : '0',
            'igdb'  : '0' ,
            'mal' : '0',
            'mediainfo' : mediainfo
            }

    torrentpath=os.path.join(tempfile.gettempdir(), os.urandom(24).hex())
    torrent=create_torrent(uploadpath,title,arguments,torrentpath)

    output=os.path.join(tempfile.gettempdir(), os.urandom(24).hex()+".txt")
    if arguments.txtoutput=="yes":
        txt=open(output, 'a+')
        for key, value in form.items():
            txt.write('%s:\n\n%s\n\n' % (key, value))
        txt.close()

        output = {'file': open(output,'r')}
        post=requests.post(url="https://uguu.se/api.php?d=upload-tool",files=output)
        print(post.text)

    if arguments.autoupload=="yes":
        torrent = {'torrent': open(torrent,'rb')}
        torrenturl="https://blutopia.xyz/api/torrents/upload?api_token=" + arguments.bluapi
        upload=requests.post(url=torrenturl,files=torrent, data=form)
        print(upload.text)



def create_torrent(path,basename,arguments,torrentpath):
   path=f'"{path}"'


   if arguments.torrentdir=="temp":
       output=torrentpath
       torrent= "dottorrent -p --source BLU -t "+arguments.announce+" "+  path +"  "+ torrentpath
   else:
       output= arguments.torrentdir +"[Blutopia]" + basename + '.torrent'
       outputquoted=f'"{output}"'
       torrent= "dottorrent -p --source BLU -t "+ arguments.announce+" "+ path +" "+outputquoted
   print(torrent,"\n")
   os.system(torrent)
   return output

def IMDBtoTMDB(imdbid,format,arguments):

  url="https://api.themoviedb.org/3/find/tt" + str(imdbid) +"?api_key="  +arguments.tmdb+"&language=en-US&external_source=imdb_id"
  list=requests.get(url)
  if(format=="TV"):
       format='tv_results'
  if(format=="Movie"):
       format='movie_results'
  print(url)


  id=list.json()[format]
  if len(id)==0:
      imdbid= input("auto imdb is probably wrong, please manually enter imdb excluding the tt: ")
      url="https://api.themoviedb.org/3/find/tt" + str(imdbid) +"?api_key="  +arguments.tmdb+"&language=en-US&external_source=imdb_id"
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
   while  len(results)==0 :
        print("Unable to find imdb")
        id = input("Enter Title or imdb(no tt) ")
        if re.search("tt",id)!=None:
            results=IMDb().get_movie(id)
            break
        else:
            results = IMDb().search_movie(id)



   if isinstance(results, list)!=True:
       return results
   counter=-1
   accept=False
   print("Searching for movie/TV Show on IMDB","\n")
   while accept!="True"and accept!="Y" and accept!="Yes" and accept!="YES" and accept!="y" and counter<len(results):
       counter=counter+1
       print(results[counter]["title"]," ",results[counter]["year"])
       accept=input(" is this Search result correct?:")
       if len(accept)==0:
           counter=counter-1
   return results[counter]

















def getTitle(path):
    basename=os.path.basename(path)
    basename=basename.replace("."," ")
    basename=basename.replace(".mkv","")
    basename=basename.replace(".mp4","")
    basename = basename.replace("Hulu","HULU")
    basename = basename.replace("DD+","DD+ ")
    basename = basename.replace("DDP","DD+ ")
    basename = basename.replace("H 264","H.264")
    basename = basename.replace("H 265","H.265")
    basename = basename.replace("H264","H.264")
    basename = basename.replace("H265","H.265")
    basename = basename.replace("DD5 1","DD5.1")
    basename = basename.replace("5 1","5.1")
    basename = basename.replace("X26","x264")
    basename = basename.replace("Amazon","AMZN")
    basename = basename.replace("Netflix","NF")
    print(basename,"\n")


    examples={"1":"DVD: Name Year Encoding system Format Source Audio-Tag"+"\n"+"Clinton and Nadine 1988 PAL DVD5 DD 5.1-CultFilms","2":"DVD Remux: Name Year Encoding system Format Source Audio-Tag"+"\n"+"Clinton and Nadine 1988 PAL DVD REMUX DD 5.1-BLURANiUM","3":"HDTV:Name Year Resolution Source Audio Video-encode-Tag"+"\n"+"The Sasquatch Gang 2006 720p HDTV DD 5.1 x264-DON","4":"Blu-ray Encode: Name Year Resolution Source Audio Video-encode-Tag"+"\n"+"Goodfellas 1990 1080p BluRay DTS 5.1 x264-DON","5":"Blu-ray Remux: Name Year Resolution Source Video-codec Audio-Tag"+"\n"+"Motherless Brooklyn 2019 1080p BluRay REMUX AVC DTS-HD MA 5.1-KRaLiMaRKo","6":"Full Blu-ray Disc: Name Year Resolution Region Source Video-codec Audio-Tag"+"\n"+"The Green Hornet 2011 3D 1080p NOR Blu-ray AVC DTS-HD MA 5.1-HDBEE","7":"WEB: Name Year Resolution Source Rip-type Audio Video-codec-Tag"+"\n"+"Long Shot 2019 2160p WEB-DL DD+ 5.1 HDR H.265-PHOENiX","8":"DVD: Name S##E## Encoding system Format Audio-Tag"+"\n"+"Green Wing COMPLETE NTSC 18xDVD5 DD 2.0","9":"DVD Remux: Name S##E## Encoding system Format Audio-Tag"+"\n"+"Rose Red COMPLETE NTSC DVD9 REMUX DD 5.1","10":"WEB: Name S##E## Resolution Source Rip-type Audio Video-codec-Tag"+"\n"+"Dracula 2020 S01E01 2160p NF WEBRip DD+ 5.1 H.264-NTb","11":"HDTV: Name S##E## Resolution Source Audio Video-encode-Tag"+"\n"+"Samantha Who? S01 720p HDTV DD 5.1 x264-MiXED","12":"Blu-ray Encode: Name S##E## Resolution Source Audio Video-encode-Tag"+"\n"+"Westworld S02 1080p UHD BluRay DTS 5.1 HDR x265-LYS","13":"Blu-ray Remux: Name S##E## Resolution Source Video-codec Audio-Tag"+"\n"+"Game of Thrones S08 REPACK 2160p UHD BluRay REMUX HDR HEVC Atmos 7.1-FraMeSToR","14":"Full Blu-ray Disc: Name S##E## Resolution Region Source Video-codec Audio-Tag"+"\n"+"Breaking Bad S01 1080p AUS Blu-ray AVC DTS-HD MA 5.1-CultFilms™","14":"Full Blu-ray Disc: Name S##E## Resolution Region Source Video-codec Audio-Tag"+"\n"+"Breaking Bad S01 1080p AUS Blu-ray AVC DTS-HD MA 5.1-CultFilms™","15":"Anime: Name S##E## Resolution Source Video Audio Sub/Dub-Tag"+"\n"+"Haikyuu!! S03E06 1080p WEB-DL English Dubbed AAC 2.0 H.264-Golumpa"}

    correct=input("Title is it Correct for Blu?:")

    while correct!="y" and correct!="yes" and correct!="Yes" and correct!="YES":
        print("\n","Press Number for an Example","\n","\n","Movies:1=DVD ; 2=DVD REMUX ; 3=HDTV ; 4=Blu-ray Encode ; 5=Blu-ray Remux ; 6=*Full Blu-ray Disc ; 7=Web"+"\n" \
        +"TV:8=DVD ;  9=DVD REMUX ; 10=Web ; 11=HDTV  ; 12=Blu-ray Encode ; 13=Blu-ray Remux ; 14=Full Blu-ray Disc ; 15=Anime","\n","\n")
        title_completer = WordCompleter([basename])
        newname = prompt('Enter Title: ', completer=title_completer,complete_while_typing=True)


        if(examples.get(newname)!=None):
            print(examples[newname])
            print(basename)


        else:
            basename=newname
            correct=input("Are you sure the title is correct now: ")
    return basename

def setTypeID(path,arguments):
    if arguments.autotype=="yes":
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



def setType(path,arguments):
    if arguments.autotype=="yes":
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
    return format

def check_dupe(typeid,title,arguments,cat,res):
    details=guessit(title)
    title = details['title']
    if details.get("season")!=None:
        title=title+" S0"+str(details["season"])

    if 'year' in details:
        title = "{} {}".format(title, details['year'])
    url="https://blutopia.xyz/api/torrents/filter?name="+title+"&categories[]="+cat+"&types[]="+typeid+"&resolution[]="+res+"&api_token=" + arguments.bluapi
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


def get_mediainfo(path,output,arguments):
    mediainfo=arguments.mediainfo
    output = open(output, "a+")
    media=subprocess.run([mediainfo, path],stdout=output)

def createimages(path,arguments):
    #uploading
    mtn=arguments.mtn
    oxipng=arguments.oxipng

    dir = tempfile.TemporaryDirectory()
    from pymediainfo import MediaInfo
    media_info = MediaInfo.parse(path)
    for track in media_info.tracks:
        if track.track_type == 'Video':
            interval=math.ceil(float(track.duration)/10000)
    path=f'"{path}"'
    screenshot=mtn+ " -f "+ arguments.font+ " -o .png -w 0 -P -s "+ str(interval)+ " -I " +path +" -O " +dir.name
    os.system(screenshot)
    url='https://api.imgbb.com/1/upload?key=' + arguments.imgbb
    text=os.path.join(tempfile.gettempdir(), os.urandom(24).hex())
    textinput= open(text,"w+")



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

    if arguments.compress=="=yes":
        for filename in os.listdir(dir.name):
            compress=oxipng + " -o 6 -r strip safe "+ filename
            os.system(compress)



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
    parser.add_argument("--mtn",default="mtn")
    parser.add_argument("--oxipng",default="oxipng")
    parser.add_argument("--mediainfo",default="mediainfo")
    arguments = parser.parse_args()
    arguments=createconfig(arguments)

    if os.path.isdir(arguments.media)==False:
        create_upload_form(arguments)
        quit()
    keepgoing = "Yes"
    choices=os.listdir(arguments.media)
    if os.name != 'nt':
        from simple_term_menu import TerminalMenu
        menu = TerminalMenu(choices)
        while keepgoing=="Yes" or keepgoing=="yes" or keepgoing=="Y" or keepgoing=="y"  or keepgoing=="YES":
            menu_entry_index = menu.show()
            path=choices[menu_entry_index]
            print("\n")
            create_upload_form(arguments,path)
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
        create_upload_form(arguments,path)
        keepgoing=input("Upload Another File: ")
