import onedrivesdk
from onedrivesdk.helpers import GetAuthCodeServer
from onedrivesdk.helpers import http_provider_with_proxy

# https://developer.microsoft.com/zh-cn/graph/quick-start 取得 ID 和 SECRET
# https://github.com/OneDrive/onedrive-sdk-python  code

proxy = {
    'http': 'http://localhost:8080',
    'https': 'https://localhost:8080'
}


#
#  透過在 https://docs.microsoft.com/zh-tw/onedrive/developer/rest-api/getting-started/app-registration?view=odsp-graph-online
#  建立好的 redirect_uri 以及 client-id , client-secret 與onedrive建立連線
#  scopes 類似於參數 可以選要建立怎麼樣的連線
#  Param : client  所有操作皆要透過client
def getService():
    redirect_uri = 'http://localhost:8080/'
    client_secret = 'zuinSN683;%]xbrINSTY51#'
    client_id = '09ec3860-34c1-4ceb-930e-30beb4de49a7'
    scopes = ['wl.signin', 'wl.offline_access', 'onedrive.readwrite']
    client = onedrivesdk.get_default_client(
        client_id='09ec3860-34c1-4ceb-930e-30beb4de49a7', scopes=scopes)
    auth_url = client.auth_provider.get_auth_url(redirect_uri)
    # this will block until we have the code
    code = GetAuthCodeServer.get_auth_code(auth_url, redirect_uri)
    client.auth_provider.authenticate(code, redirect_uri, client_secret)

    return client


#  新增資料夾
def addFolder(folderName, client):
    f = onedrivesdk.Folder()
    i = onedrivesdk.Item()
    i.name = folderName
    i.folder = f
    returned_item = client.item(drive='me', id='root').children.add(i)


#  取得現在路徑底下所有檔案的Id
def getrootAllFileID(client):
    root_folder = client.item(drive='me', id='root').children.get()
    for i in range(len(root_folder)):
        print(root_folder[i].id)
        print("     " + str(root_folder[i].name))


#  透過某一個資料夾的id, 印出該資料夾底下所有檔案
def getFileIdBy(client, fileid):
    root_folder = client.item(drive='me', id=fileid).children.get()
    for i in range(len(root_folder)):
        print(root_folder[i].id)
        print("     " + str(root_folder[i].name))


#  透過名稱找到 目標檔案底下該檔案的ID
def getFileIdByNameUnderID(client, fileName, underfileid):
    root_folder = client.item(drive='me', id=underfileid).children.get()
    for i in range(len(root_folder)):
        if root_folder[i].name == fileName:
            return root_folder[i].id

    return None


#  上傳檔案到OneDrive
def uploadFile(client, Uplaodname, filePathinLocal, uploadFolderId):
    returned_item = client.item(drive='me', id=uploadFolderId).children[Uplaodname].upload(filePathinLocal)


#  從OneDrive下載檔案
def downloadFile(client, fileId, downloadPath):
    # root_folder = client.item(drive='me', id='root').children.get()
    id_of_file = fileId
    client.item(drive='me', id=id_of_file).download(downloadPath)


#  重新命名OneDrive上面的檔案
def renameFile(client, newName, fileId):
    renamed_item = onedrivesdk.Item()
    renamed_item.name = 'newName'
    renamed_item.id = fileId

    new_item = client.item(drive='me', id=renamed_item.id).update(renamed_item)
