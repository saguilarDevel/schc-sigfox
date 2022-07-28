# SCHC-over-SigFox

## Objectives

While testing the integration between LoPy4-SigFox-GCF, it becomes difficult to perform testing in an efficient way due to the time requiered to upload code and check the result logs.

To solve this issue, a local flask server is build to simulate the behaviour of the Google Cloud Function and a Rest client is used to simulate the message posting. This allows local testing to debug the code that will be deploy to google cloud.

## Setup

Create a folder called credentials.
Download the credentials from Google Cloud.

To get the credentials, go to Google Cloud Console.
Go to APIs & Services.
Go to Credentials.

In Credentials, click "Create Credentials", "Service Account". 
Give name, Service account ID and description. 

Download "your_credentials.json" to the /credentials folder created before. 

In config/config.py, replace the PATH to your credential file.
```
CLIENT_SECRETS_FILE = '/PATH/credentials/your_credentials.json'
```

Also update the Bucket name used for the storage.

```
BUCKET_NAME = 'your-bucket-name'
```
##Execution


* In the diego_experiments_v2 branch of schc-sigfox, change the config parameters about the GCP and Firebase accounts and then run the deploy.py script. This will upload the main.py functions to CF.

* Set the callback in the Sigfox backend in the following style, including the quotes (") in enable_losses and enable_dl_losses:
```text
{
    "deviceType" : "01b29fc5",
    "device" : "{device}",
    "time" : "{time}",
    "data" : "{data}",
    "seqNumber" : "{seqNumber}",
    "ack" : "{ack}",
    "loss_rate" : 10,
    "enable_losses" : "True",
    "enable_dl_losses" : "False"
}
```

* In the diego_test_v2 branch of schcFox, upload it to the LoPy. That will run the main.py script.

    * In the config.py script you can select what packet size you want to send.
    * Running the main.py script will run these experiments for all packet sizes specified in config.py and save their data in the "stats" directory.
    * After a set of experiments, download files from the Lopy. This will add new files to the "stats" directory on the PC.
    * If running an UL+DL loss case, open the Firebase Realtime Database. 
You will find files named "DL_LOSSESS_N". 
These files record the messages that were artificially lost in downlink.

        * The DL_LOSSES_N file has the experiment number and window number where a DL loss was induced. Write these values to any text file in your computer, including the packet size and FER that you just sent.
        
    * Move the files from the "stats" directory to the "results" one, inside the folder that corresponds (for example, results/ul_10 shall have the results of the 10% uplink FER case).
    * Run the delete_data.py script. This will erase everything inisde the "stats" directory (except for the dummy.txt file, which is necessary for the folder to be recognized in the Lopy)
    * Add the "results" directory to the pyignore list in Atom. This will prevent its files to be uploaded every time the code is uploaded to the Lopy.
    * Upload the code to the Lopy again, and repeat all the steps.
    
    
* After getting all the results that you want, push them to the schcFox repo if you're using another PC (try making another branch first, as I am currently using this one in these experiments). If the data analysis will be executed in the same PC that is connected to the Lopy, ignore this step.
* The SCHCLogger class has a extract_data() method that is commented out. Uncomment it (you can select many lines in Pycharm pressing and dragging the mouse wheel I think).
    * The extract_data() method reads the JSON file of an individual experiment and writes the data to an output.txt file and an Excel spreadsheet.
* In the results folder there exists an Excel spreadsheet named "Template.xlsx". Rename it to "Template Results UL.xlsx", copy it and rename its copy to "Template Results ULDL.xlsx". These templates will be empty aside from the functions used to calculate statistics about the data.
* Run the extract_data.py script. This scripts needs that you have the template I've been using inside the results folder, named "Template Results UL.xlsx" or "Template Results ULDL.xlsx" (of course, you can change these names in the code).
    * This script will run the extract_data() method for every JSON file, for every folder in the "results" folder.
    * The results will be written automatically in the spreadsheet. When you open it, the results and bar graphs just processed will be ready.
    * If running an UL+DL loss case, open your text file where the DL_LOSSES_N data was written. These values shall be added manually to the spreadsheet:
        * N is the experiment number, so you can check for the column inside the spreadsheet for the packet size and the FER specified.
        * Check the text that correspond to DL_LOSSES_N: It says something like "lost DL message in window M". If M equals the window number of the final window, write how many messages were lost in the same window in the row "All-1 Fragments / DL Errors". If I'm not mistaken, this row has the number 22.
        * If M is not the final window number, write hoy many messages were lost in every window that is not the last one in the row "All 0 Fragments / DL Errors". If I'm not mistaken, this row has the number 14.
        
That's it. The fundamental steps are:

1. Upload the functions of schc-sigfox to CF using the deploy.py script.
2. Configure the callback in the Sigfox backend.
3. Upload the code of schcFox to the Lopy (this will run the main.py script) and wait for the experiments to be completed.
4. Download stats files from the Lopy and move them to their respective folder.
5. If running a UL+DL loss case, save the DL_LOSSES_N data.
6. Run the delete_data.py script in the Lopy
7. Repeat from step 2 for every FER (in our set of experiments, this is done 4 times).
8. Uncomment the extract_data() method in SCHCLogger and run the extract_data script in the PC.
9. For UL+DL loss cases, write the DL_LOSSES_N data in the spreadsheets.

The automation of these experiments needs every step to be executed in order, so please tell me if you have any doubts or problems regarding these steps. You can also modify the config.py and extract_data.py scripts if you want to run or analyze individual FER experiments. Note that the DL_LOSSES_N data recollection is not yet automated, but it can be done easily.   


