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
ia = IMDb()
import pickle
import subprocess
import configparser
config = configparser.ConfigParser(allow_no_value=True)

#TODO
#mal
def get_mediainfo(path,output,arguments):
    mediainfo=arguments.mediainfo
    output = open(output, "a+")
    media=subprocess.run([mediainfo, path],stdout=output)


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
    if arguments.anon==None:
        arguments.anon=config['general']['anon']
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
    if arguments.oxipng=="mediainfo" and len(config['general']['mediainfo'])!=0:
        arguments.mediainfo=config['general']['mediainfo']
    if arguments.compress==None and config['general']['compress']=="yes":
        arguments.compress=config['general']['compress']

    return arguments


def createimages(path,arguments):
    #uploading
    mtn=arguments.mtn
    oxipng=arguments.oxipng
    path=f'"{path}"'
    dir = tempfile.TemporaryDirectory()
    screenshot=mtn+ " -f "+ arguments.font+ " -o .png -w 0 -s 400 -I " +path +" -O " +dir.name
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
    os.chdir(dir.name)

    if arguments.compress=="=yes":
        for filename in os.listdir(dir.name):
            compress=oxipng + " -o 6 -r strip safe "+ filename
            os.system(compress)



    for filename in os.listdir(dir.name):
       filename=dir.name+'/'+filename
       image=filename
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
    return textoutput.read()


def setCat(format):
    if format=="Movie":
        return "1"
    if format=="TV":
        return "2"


def create_upload_form(arguments,entyname=None):
    if entyname==None:
        path=arguments.media
    else:
        path=arguments.media+entyname
    output=os.path.join(tempfile.gettempdir(), os.urandom(24).hex()+".txt")

    title=getTitle(path)
    torrentpath=os.path.join(tempfile.gettempdir(), os.urandom(24).hex())
    torrent=create_torrent(path,title,arguments,torrentpath)

    if Path(path).is_dir():
        path = str(next(Path(path).glob('*/')))
    imdbid = getimdb(path)
    format = setType(path,arguments)


    tmdbid=IMDBtoTMDB(imdbid.movieID,format,arguments)
    mediapath=os.path.join(tempfile.gettempdir(), os.urandom(24).hex())
    media=get_mediainfo(path,mediapath)

    media=open(mediapath, 'r').read()

    form = {'imdb' : imdbid.movieID,
            'name' : title,
            'description' : createimages(path,arguments),
            'category_id' : setCat(format),
            'tmdb': tmdbid,
            'type_id': setTypeID(path,arguments),
            'resolution_id' : setResolution(path),
            'mediainfo' : media,
            'user_id' : arguments.userid,
            'anonymous' : arguments.anon,
            'stream'    : arguments.stream,
            'sd'        : is_sd(path),
            'tvdb'      : '0',
            'igdb'  : '0' ,
            'mal' : '0'
            }




    #send temp paste
    if arguments.txtoutput=="yes":

        txt=open(output, 'w')
        for key, value in form.items():
            txt.write('%s:\n\n%s\n\n' % (key, value))

        with open(output, 'a+') as outfile:
            outfile.write('%s:\n\n' % ('media:'))
            #Open each file in read mode
            with open(mediapath) as infile:
                outfile.write(infile.read())

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
       torrent= "dottorrent -p -t "+arguments.announce+" "+  path +"  "+ torrentpath
   else:
       output= arguments.torrentdir +"[Blutopia]" + basename + '.torrent'
       outputquoted=f'"{output}"'
       torrent= "dottorrent -p -t "+ arguments.announce+" "+ path +" "+outputquoted
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
      imdb = input("auto imdb is probably wrong, please manually enter imdb excluding the tt: ")
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
   if len(results) ==0:
        print("Unable to find imdb")
        id = input("Enter imdb just what comes after tt: ")
        id=IMDb().get_movie(id)
   else:
       id=IMDb().search_movie(title)[0]
   return id














def getTitle(path):
    basename=os.path.basename(path)
    basename=basename.replace("."," ")
    basename = basename.replace("H 264","H.264")
    basename = basename.replace("H 265","H.265")
    basename = basename.replace("H264","H.264")
    basename = basename.replace("H265","H.265")
    basename = basename.replace("DD5 1","DD5.1")
    basename = basename.replace("5 1","5.1")
    basename = basename.replace("X26","x264")
    basename = basename.replace("Amazon","AMZN")
    basename = basename.replace("Netflix","NF")
    return basename

def setTypeID(path,arguments):
    if arguments.autotype=="yes":
        details=guessit(path)
        source = details['source']
        remux=details.get('other')



        if (source=="Blu-ray" or source=="HD-DVD" or source=="Ultra HD Blu-ray") and remux==None:
            source = '12'
        elif (source=="Blu-ray" or source=="HD-DVD" or source=="Ultra HD Blu-ray") and remux!=None:
            source = '3'
        elif source=="Web" and remux=="remux":
            source = '4'
        elif source=="Web" and remux!="remux":
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
    for enty in os.scandir(arguments.media):
        path=arguments.media+enty.name
        print(path)
        upload = input("Do you want to upload this torrent yes or no: ")
        if upload=="yes" or upload=="Yes" or upload=="Y" or upload=="y"  or upload=="YES":
            create_upload_form(arguments,enty.name)
