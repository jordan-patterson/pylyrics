#!/usr/bin/env python3
from curses import *
import json
import re
import os
import requests
from bs4 import BeautifulSoup

#text displayed on status bar
status_bar_text="   [?]HELP | [q]QUIT | [s]SEARCH | [h]HOME | [f]FAVORITE"
user_dir=os.getenv("HOME")
#directory where file is stored
favorited_dir=user_dir+"/bin/pylyrics/favorites.json"
#api key
client_token="y_m45kUiZe6VcQErrhydp_K20Ckc3V85ICQ2-lH_k8wbu43D0jirkZA6Mqqnc2CZ"
UP=65
DOWN=66
ENTER=10

class Result:
    def __init__(self,title,url):
        self.title=title
        self.url=url

    def getLyrics(self):
        lyrics=[]
        lines=''
        r=requests.get(self.url)
        if(r.status_code==200):
            soup=BeautifulSoup(r.text)
            parags=soup.find_all("p")
            for i in parags:
                lines+=i.text
            for line in lines.split('\n'):
                lyrics.append(line)
        return lyrics

    def printLyrics(self):
        lines=getLyrics(self.url)
        for line in lines:
            print(line)

def getResults(query):
    """
	   returns a list of result objects from search
    """
    results=[]
    query=re.sub("[^\w\+]+","+",query)#replaces all spaces in query with '+'
    access={"access_token":client_token}
    r=requests.get("https://api.genius.com/search?q={}".format(query),params=access)
    if(r.status_code==200):
        try:
            data=json.loads(r.text)
            songs=data["response"]["hits"]
            if len(songs)>0:
                for s in songs:
                    title=s["result"]["full_title"]
                    url=s["result"]["url"]
                    res=Result(title,url)
                    results.append(res)
        except:
            pass
    return results

def getfavs():
    #returns dictionary of favorited songs
    songs=[]
    try:
        with open(favorited_dir,'r') as file:
            data=json.load(file)
            for s in data.items():
                title=s[0]
                url=s[1]
                song=Result(title,url)
                songs.append(song)
        return songs
    except:
        return None

def favorite(song):
    #adds song to favorites
    title=str(song.title)
    url=str(song.url)
    try:
        #open file for reading
        with open(favorited_dir,'r') as file:
            data=json.load(file)
            if title not in data.keys():
                data[title]=url
        #open file for writing
        with open(favorited_dir,'w') as file:
            json.dump(data,file)
    except:
        #initialize new file/directory
        if not os.path.exists(favorited_dir):
            directory=os.path.dirname(favorited_dir)
            os.mkdir(directory)
            os.chdir(directory)
            file=open(favorited_dir,'w')
            data={title:url}
            json.dump(data,file)
            file.close()

def getResponsiveText(width,text):
    '''
        returns a list of lines to render to current screen
    '''
    lines=[]
    #split text into words
    words=text.split(' ')
    i=0#index marker
    while True:
        #variable to store fitted line based on screen width
        line=''
        #loop through words
        for word in words[i:]:
            #add word to line
            line+=word+' '
            i+=1
            #check if line fits screen length
            try:
                if(len(line+words[i])>width-3):
                    lines.append(line)
                    break
            except:
                #all words have been exhausted
                lines.append(line)
                return lines

def getCenterx(text,max_x):
    '''
        returns the center x position where text would be centered
    '''
    length=len(text)
    center_x=int((max_x//2)-(length//2))
    return center_x

class Window():
    def __init__(self,status_bar_text):
        self.title="PYLYRICS"
        self.screen=initscr()
        self.height,self.width=self.screen.getmaxyx()
        #colors
        start_color()
        init_pair(1,COLOR_WHITE,COLOR_BLACK)
        init_pair(2,COLOR_YELLOW,COLOR_BLACK)
        init_pair(3,COLOR_BLACK,COLOR_WHITE)
        init_pair(4,COLOR_RED,COLOR_WHITE)
        self.status_bar_text=status_bar_text

    def render_songs(self,songs,win,position):
        win_width=int(self.width/2)#across
        win_length=int(self.height)-10#down
        start_y=6
        for i in range(len(songs)):
            title=songs[i].title
            if i==position:
                win.attron(color_pair(3))
            try:
                win.addstr(start_y+i,getCenterx(title,win_width),title)
            except:
                pass
            if i==position:
                win.attroff(color_pair(3))


    def lyrics(self,win,lyrs,topline,bottomline):
        #renders song lyrics on subwindow
        win_width=int(self.width/2)#across
        win_length=int(self.height)-10#down
        starty=4
        for i in range(win_length-10):
            try:
                win.addstr(starty+i,2,lyrs[topline+i])
            except:
                pass
                '''
                lines=getResponsiveText(lyrs[topline+i])
                for j in range(len(lines)):
                    win.addstr(starty+j,2,lines[j])
                starty+=len(lines)+1
                '''

    def home(self,win,songs,position):
        #renders elements on home screen
        win_width=int(self.width/2)#across
        win_length=int(self.height)-10#down
        if(songs==None):
            msg="YOU HAVE NO FAVORITED SONG LYRICS."
            smsg="PRESS 's' to SEARCH FOR A SONG"
            self.screen.attron(color_pair(1))
            try:
                win.addstr(5,getCenterx(msg,win_width),msg)
                win.addstr(7,getCenterx(smsg,win_width),smsg)
            except:
                start_y=5
                msg_list=getResponsiveText(win_width,msg)
                for i in range(len(msg_list)):
                    try:
                        win.addstr(start_y+i,1,msg_list[i])
                    except:
                        pass
                start_y=5+len(msg_list)+2
                smsg_list=getResponsiveText(win_width,smsg)
                for i in range(len(smsg_list)):
                    try:
                        win.addstr(start_y+i,1,smsg_list[i])
                    except:
                        pass
        else:
            self.render_songs(songs,win,position)
        self.screen.attroff(color_pair(1))

    def help(self,win):
        #help screen
        win_width=int(self.width/2)#across
        win_length=int(self.height)-10#down
        start_y=4
        commands=[]
        commands.append("'q' - Exit the program")
        commands.append("'s' - Search for a song")
        commands.append("'h' - Return to home screen")
        commands.append("'f' - Add song to favorites")
        pos=4
        for command in commands:
            try:
                win.addstr(pos,getCenterx(command,win_width),command)
                win.addstr(pos+1,1,"  ")
                pos+=2
            except:
                pass
        #win.addstr(start_y,2,"This is a test")

    def search(self,win,query,results,position):
        win_width=int(self.width/2)#across
        win_length=int(self.height)-10#down
        self.screen.attroff(A_BOLD)
        self.screen.attron(color_pair(2))
        fdback="SEARCH RESULTS FOR "+str(query)
        try:
            win.addstr(4,getCenterx(fdback,win_width),fdback)
        except:
            lines=getResponsiveText(win_width,fdback)
            start_y=4
            for i in range(len(lines)):
                try:
                    win.addstr(start_y+i,1,lines[i])
                except:
                    pass
        if(len(results)==0):
            try:
                msg="NO RESULTS WERE FOUND FOR {}".format(query)
                win.addstr(8,getCenterx(msg,win_width),msg)
            except:
                lines=getResponsiveText(win_width,msg)
                start_y=8
                for i in range(len(lines)):
                    try:
                        win.addstr(start_y+i+1,1,lines[i])
                    except:
                        pass
        else:
            start_y=7
            #loop through search results
            for i in range(len(results)):
                if(i==position):
                    win.attron(color_pair(3))
                try:
                    title=results[i].title
                    win.addstr(start_y+i+1,getCenterx(title,win_width),title)
                except:
                    pass
                if(i==position):
                    win.attroff(color_pair(3))
            '''
            title=results[0].title
            win.addstr(start_y,getCenterx(title,win_width),title)
            '''
        self.screen.attron(A_BOLD)
        win.scrollok(True)

    def run(self):
        key=-1
        song=Result("defautl","default")
        cur_state="HOME"
        lyrics=[]
        topline,bottomline=0,10#used to mark index of top and bottom line of text
        fav_position=0
        while True:
            self.screen.clear()
            self.height,self.width=self.screen.getmaxyx()
            #calculations for topbar space
            space_len=((int(self.width)-len(cur_state))//2)
            #set attributes for top bar
            self.screen.attron(color_pair(3))
            self.screen.attron(A_BOLD)
            state_x=getCenterx(cur_state,self.width)
            try:
                #add left space
                self.screen.addstr(0,0," "*space_len)
                self.screen.addstr(0,state_x,cur_state)#add current state string
                #add right space
                right_space_x=len(cur_state)+space_len
                self.screen.addstr(0,right_space_x," "*space_len)
                #calculations for centering title
                title_x=getCenterx(self.title,self.width)
                title_y=int(self.height//8)
                #set attributes for title
                self.screen.attron(color_pair(1))
                #render title
                self.screen.addstr(title_y,title_x,self.title)
                self.screen.attroff(color_pair(1))
            except:
                pass
            subtitles={"HOME":"FAVORITED SONGS","SEARCH":"SEARCH RESULTS","HELP":"HELP","LYRICS":song.title}
            #sub-window size calculations
            beginx=int((self.width//2)/2)
            beginy=title_y+2
            win_width=int(self.width/2)#across
            win_length=int(self.height)-10#down
            try:
                #initialize sub-window
                win=self.screen.subpad(win_length,win_width,beginy,beginx)
                win.attron(color_pair(3))
                #calculate length of spaces on both sides of subtitle
                top_space_len=((int(win_width)-len(subtitles[cur_state]))//2)
                win.addstr(1,0," "*top_space_len)
                win.addstr(1,getCenterx(subtitles[cur_state],win_width),subtitles[cur_state])
                win.addstr(1,len(subtitles[cur_state])+top_space_len," "*top_space_len)
                win.attroff(color_pair(3))
                win.box()
            except:
                pass
            #render elements based on active state
            if cur_state=="HOME":
                favs=getfavs()
                self.home(win,favs,fav_position)
            elif cur_state=="SEARCH":
                #render search results here
                self.search(win,query,results,position)
            elif cur_state=="HELP":
                self.help(win)
            elif cur_state=="LYRICS":
                    self.lyrics(win,lyrics,topline,bottomline)
            #render status bar
            self.screen.attron(color_pair(3))
            try:
                self.screen.addstr(self.height-1,0,self.status_bar_text)
                space_len=int(self.width)-len(self.status_bar_text)-1
                self.screen.addstr(self.height-1,len(self.status_bar_text)," "*space_len)
            except:
                pass
            self.screen.attroff(color_pair(3))#turn off attribute
            #refresh screen
            self.screen.refresh()
            key=self.screen.getch()
            if key==ord('q') or key==ord('Q'):
                '''
                    prompt if user actually wants to quit here
                    if input=='y' break else continue
                '''
                break
            elif key==ord('?'):
                cur_state="HELP"
            elif (key==UP or key==DOWN) and cur_state=="SEARCH":
                #update position of highlighted text in search function
                if key==UP and position>0:
                    position=position-1
                elif key==DOWN and position<len(results)-1:
                    position=position+1
                self.search(win,query,results,position)
                #cur_state="HOME"
            elif key==ord('s') or key==('S'):
                prompt_text="   ENTER THE NAME OF A SONG: "
                self.screen.attron(color_pair(3))
                try:
                    #adding prompt text
                    self.screen.addstr(int(self.height-1),0,prompt_text)
                    space_len=int(self.width)-len(prompt_text)-1
                    self.screen.addstr(int(self.height-1),len(prompt_text)," "*space_len)
                    self.screen.attroff(color_pair(3))#turn off attribute
                except:
                    pass
                self.screen.refresh()
                echo()
                self.screen.attron(color_pair(4))
                new_query=self.screen.getstr(self.height-1,len(prompt_text))
                self.screen.attroff(color_pair(4))
                if(new_query):
                    query=new_query.decode('utf-8')
                    results=getResults(query)
                    cur_state="SEARCH"
                    position=0
            elif key==ord('h') or key==('H'):
                cur_state="HOME"
            elif key==10 and cur_state=="SEARCH":#user presses enter on search screen
                if(len(results)>0):
                    try:
                        song=results[position]
                        lyrics=song.getLyrics()
                    except:
                        pass
                    cur_state="LYRICS"
            elif(key==UP or key==DOWN) and cur_state=="LYRICS":
                if key==DOWN and bottomline<len(lyrics):
                    topline=topline+1
                    bottomline=bottomline+1
                elif key==UP and topline>0:
                    topline=topline-1
                    bottomline=bottomline-1
            elif key==ord('f') and cur_state=="LYRICS":
                favorite(song)
            elif(key==UP or key==DOWN or key==ENTER) and cur_state=="HOME":
                #update position based on arrow keys
                if key==DOWN and fav_position<len(favs)-1:
                    fav_position=fav_position+1
                elif key==UP and fav_position>0:
                    fav_position=fav_position-1
                elif key==ENTER:
                    song=favs[fav_position]
                    lyrics=song.getLyrics()
                    cur_state="LYRICS"

def main():
    window=Window(status_bar_text)
    wrapper(window.run())
    echo()
    endwin()

if __name__=="__main__":
    '''
        Written by Jordan Patterson.
    '''
    try:
        main()
    except:
        pass
