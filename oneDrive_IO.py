import onedrivesdk
from onedrivesdk.helpers import GetAuthCodeServer
from onedrivesdk.helpers import http_provider_with_proxy

# https://developer.microsoft.com/zh-cn/graph/quick-start 取得 ID 和 SECRET
# https://github.com/OneDrive/onedrive-sdk-python  code

proxy = {
    'http': 'http://localhost:8080',
    'https': 'https://localhost:8080'
}


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


def addFolder(folderName, client):
    f = onedrivesdk.Folder()
    i = onedrivesdk.Item()
    i.name = folderName
    i.folder = f
    returned_item = client.item(drive='me', id='root').children.add(i)


def getrootAllFileID(client):
    root_folder = client.item(drive='me', id='root').children.get()
    for i in range(len(root_folder)):
        print(root_folder[i].id)
        print("     " + str(root_folder[i].name))


def getFileIdBy(client, fileid):
    root_folder = client.item(drive='me', id=fileid).children.get()
    for i in range(len(root_folder)):
        print(root_folder[i].id)
        print("     " + str(root_folder[i].name))


def getFileIdByNameUnderID(client, fileName, underfileid):
    root_folder = client.item(drive='me', id=underfileid).children.get()
    for i in range(len(root_folder)):
        if( root_folder[i].name == fileName ):
            return root_folder[i].id

    return None


def uploadFile(client, Uplaodname, filePathinLocal, uploadFolderId):
    returned_item = client.item(drive='me', id=uploadFolderId).children[Uplaodname].upload(filePathinLocal)


def downloadFile(client, fileId, downloadPath):
    # root_folder = client.item(drive='me', id='root').children.get()
    id_of_file = fileId

    client.item(drive='me', id=id_of_file).download(downloadPath)


def renameFile(client, newName, fileId):
    renamed_item = onedrivesdk.Item()
    renamed_item.name = 'newName'
    renamed_item.id = fileId

    new_item = client.item(drive='me', id=renamed_item.id).update(renamed_item)