from __future__ import print_function
import io, os
import pickle
import os.path
import googleapiclient, httplib2, oauth2client
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from oauth2client import tools
from apiclient import discovery
from oauth2client import client

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/drive.file']

try:
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


# 取得和 Google Drive要用的credential
# token.pickle 是從google drive上面取得
def getCredential():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def getService():
    creds = getCredential()
    service = build('drive', 'v3', credentials=creds)
    return service


def getAllFileID(service):
    # Call the Drive v3 API
    results = service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))


def getFileIDbyName(service, fileName):
    # Call the Drive v3 API
    results = service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        for item in items:
            if( item['name'] == fileName ):
                return item['id']

        return None


def uploadFile(service, Uplaodname, filePathinLocal, mimetype, uploadFolderId):
    folder_id = uploadFolderId  # stock_data folder's ID, if don't specify , it will store to top directory
    file_metadata = {
        'name': Uplaodname,
        'parents': [folder_id]
    }
    media = MediaFileUpload(filePathinLocal,
                            mimetype=mimetype,
                            resumable=True)
    file = service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields='id').execute()
    print('File ID: %s' % file.get('id'))


# useless, actually same as uploadFile()
def uploadImage(service, filename, filepath, mimetype, drivefolderID):
    folder_id = drivefolderID# stock_data folder's ID, if don't specify , it will store to top directory
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    media = MediaFileUpload(filepath,
                            mimetype=mimetype)
    file = service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields='id').execute()
    print
    'File ID: %s' % file.get('id')


    # 上傳圖片
    # uploadImage(service, 'Stock_Data/cat.jpg', 'history_data/cat.jpg', 'image/jpeg', '1t-UeRyTRf_55ZGabaANlVPf8YR1zxDxT')
    # 列出檔案名稱及id
    # driveApi.printFileListandId(service)
    # 上傳文件
    # uploadFile(service=service, filename='AES.csv', filepath='history_data/AES.csv', mimetype='text/csv', drivefolderID='1t-UeRyTRf_55ZGabaANlVPf8YR1zxDxT')


def downloadFile(service, fileID, filePath):
    request = service.files().get_media(fileId=fileID)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))
    with io.open(filePath, 'wb') as f:
        fh.seek(0)
        f.write(fh.read())


def addFolder(folderName, service):
    file_metadata = {
    'name': folderName,
    'mimeType': 'application/vnd.google-apps.folder'
    }
    file = service.files().create(body=file_metadata, fields='id').execute()
    print ('Folder ID: %s' % file.get('id'))