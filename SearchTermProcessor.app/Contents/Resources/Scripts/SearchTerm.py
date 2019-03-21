import tkinter as tk
#from tkinter import simpledialog
from tkinter import filedialog
import os
from nltk.stem import WordNetLemmatizer
lemmatizer=WordNetLemmatizer()
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import numpy as np
#added to suppress errors for symbols in text fields
from contextlib import suppress

master = tk.Tk()
def fileselect():
    global dataset
    global directory
    my_filetypes = [('CSV', '.csv'), ('all files', '.*')]
    answer = filedialog.askopenfilename(parent=master,
                                        initialdir=os.path.expanduser('~'),
                                        title="Please select a file:",
                                        filetypes=my_filetypes)
    dispFile = tk.Label(master, text = answer)
    dispFile.grid(row = 0, column = 1)
    dataset = pd.read_csv(answer) 
    directory = answer.rstrip(answer[answer.rfind("/")+1:])
slctFile = tk.Button(master, text="File", width=10, command=fileselect)
slctFile.grid(row = 0, column = 0)
slctFile.focus_set()
def callback():
   master.withdraw()
   master.quit()
   master.destroy()
sve = tk.Button(master, text="Save", width=10, command=callback)
sve.grid(row = 1)
tk.mainloop()


def Lem():
    #lemmetizer
    ttlRws = int(max(dataset.index))
    rowcount=0
    while rowcount <= ttlRws:
        cmptrm = dataset.iloc[rowcount,0]
        breakdown = [cmptrm.split()]
        lwrds = []
        for i in range (0, len(breakdown)):
            l1 = breakdown[i]
            l2= " ".join(lemmatizer.lemmatize(word) for word in l1)
            lwrds.append(l2)
        dataset.loc[rowcount,'root term']= " ".join(str(x) for x in lwrds)
        rowcount = rowcount +1  

def Process():
    global dataset
    # Remove extra spaces, quotes and capitalization
    dataset['Search Term'] = dataset['Search Term'].replace('\s+', ' ', regex=True).replace('"', '', regex=True).str.lower()
    #group by Search Term and Returned
    dataset = dataset.groupby(['Search Term']).sum()
    #remove results with grouped total under 100
    dataset = dataset[dataset['Unique Events'] > 99]
    dataset = dataset.sort_values('Unique Events', ascending = 0)
    dataset.reset_index(level=['Search Term'],
                inplace=True) 
    dataset['key']=pd.to_numeric(dataset.index)

def FzzyLkUp():
    global dataset
    global final
    global directory
    ttlRws = int(max(dataset.index))
    x=0
    df = pd.DataFrame(columns=["root","location"])
    while x <= ttlRws:
        root = dataset['root term'].iloc[x]
        cmp=pd.DataFrame(np.array(process.extractBests(root,dataset['root term'],
                        scorer = fuzz.ratio,
                        score_cutoff = 91,
                        limit = 10)))
        #added a default of 0 to handle empty strings
        lstrw = int(max(cmp.index, default=0))
        i = 0
        #added to suppress errors for symbols in text fields
        with suppress(Exception):
            while i <= lstrw:
                location = cmp[2].iloc[i]
                cmpile = pd.DataFrame({"root":[root],"location":[location]})
                df = df.append(cmpile, ignore_index=True)
                i +=1
        x +=1
        
    df['location']=pd.to_numeric(df['location'])
    final = pd.merge(left=df,
               right=dataset,
               how='left',
               left_on='location',
               right_on='key',
               sort=False)
    
    final = final[['root','Search Term','Unique Events']].drop_duplicates(subset = 'Search Term',
                              keep = 'first')
    os.chdir(directory)
    final.to_csv('MonthlySiteSearch.csv')
    
Process()
Lem()
FzzyLkUp()